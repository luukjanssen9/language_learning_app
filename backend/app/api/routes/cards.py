import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.crud_utils import get_or_404
from app.database import get_db
from app.models.card import Card
from app.models.course import Course
from app.models.deck import DEFAULT_DAILY_NEW_CARD_CAP, Deck
from app.models.enums import CardDirection, CardState, ReviewRating
from app.models.language import Language
from app.models.review_log import ReviewLog
from app.models.vocabulary import VocabularyItem
from app.schemas.card import (
    CardCreate,
    CardQuickAdd,
    CardQuickAddResponse,
    CardRead,
    CardReviewResponse,
    CardReviewSubmit,
    CardUpdate,
)
from app.schemas.review_log import ReviewLogRead
from app.schemas.vocabulary import VocabularyItemRead
from app.services.fsrs_engine import apply_review
from app.services.note_cards import build_cards_for_note
from app.services.text_normalize import normalize_for_comparison

router = APIRouter(prefix="/cards", tags=["cards"])


@router.post("", response_model=CardRead, status_code=status.HTTP_201_CREATED)
async def create_card(payload: CardCreate, db: AsyncSession = Depends(get_db)) -> Card:
    card = Card(**payload.model_dump())
    db.add(card)
    await db.commit()
    await db.refresh(card, attribute_names=["vocabulary_item"])
    return card


@router.post("/quick-add", response_model=CardQuickAddResponse, status_code=status.HTTP_201_CREATED)
async def quick_add_card(
    payload: CardQuickAdd, db: AsyncSession = Depends(get_db)
) -> CardQuickAddResponse:
    """Creates one `VocabularyItem` ("note") plus the `Card`(s) it produces,
    in one round trip -- see `CardQuickAdd`'s docstring for why this is a
    separate endpoint from the plain CRUD ones above.

    Idempotent on (course, target_text, base_text), accent/case-
    insensitive: reuses an existing note (and just adds a card if this
    deck happens to be missing one for it) instead of creating a
    duplicate -- found live via the journal-correction "add to deck"
    flow, whose accept button can't (yet) tell a suggestion was already
    accepted on a prior visit. Distinct senses of a homonym (e.g. Dutch
    "bank" -> bank/couch/bench) still get their own note, since they
    differ on `base_text` -- see PLAN.md's 2026-08-14 follow-up.
    """
    deck = await get_or_404(db, Deck, payload.deck_id)
    course = await get_or_404(db, Course, deck.course_id)
    target_language = await get_or_404(db, Language, course.target_language_id)

    normalized_target = normalize_for_comparison(payload.target_text)
    normalized_base = normalize_for_comparison(payload.base_text)
    existing_items = await db.execute(
        select(VocabularyItem).where(VocabularyItem.course_id == course.id)
    )
    vocabulary_item = next(
        (
            item
            for item in existing_items.scalars()
            if normalize_for_comparison(item.target_text) == normalized_target
            and normalize_for_comparison(item.base_text) == normalized_base
        ),
        None,
    )

    if vocabulary_item is None:
        vocabulary_item = VocabularyItem(
            course_id=course.id,
            target_text=payload.target_text,
            base_text=payload.base_text,
            part_of_speech=payload.part_of_speech,
            source=payload.source,
            example_sentence=payload.example_sentence,
            example_sentence_translation=payload.example_sentence_translation,
            tags=payload.tags,
            attributes=payload.attributes,
        )
        db.add(vocabulary_item)
        await db.flush()
        cards = build_cards_for_note(deck.id, vocabulary_item.id, target_language)
        db.add_all(cards)
    else:
        existing_cards = await db.execute(
            select(Card).where(
                Card.deck_id == deck.id, Card.vocabulary_item_id == vocabulary_item.id
            )
        )
        cards = list(existing_cards.scalars())
        if not cards:
            cards = build_cards_for_note(deck.id, vocabulary_item.id, target_language)
            db.add_all(cards)

    await db.commit()
    await db.refresh(vocabulary_item)
    for card in cards:
        await db.refresh(card, attribute_names=["vocabulary_item"])

    return CardQuickAddResponse(
        vocabulary_item=VocabularyItemRead.model_validate(vocabulary_item),
        cards=[CardRead.model_validate(card) for card in cards],
    )


@router.get("", response_model=list[CardRead])
async def list_cards(
    deck_id: uuid.UUID | None = None, db: AsyncSession = Depends(get_db)
) -> list[Card]:
    query = select(Card).options(selectinload(Card.vocabulary_item)).order_by(Card.created_at)
    if deck_id is not None:
        query = query.where(Card.deck_id == deck_id)
    result = await db.execute(query)
    return list(result.scalars().all())


async def _unlock_eligible_production_cards(
    db: AsyncSession, deck_id: uuid.UUID, now: datetime
) -> None:
    """Flips a SUSPENDED production card to NEW once its sibling
    recognition card's production gate is met -- see
    `app/services/note_cards.py`'s module docstring for the config shape
    and PLAN.md's 2026-08-14 "Anki-style vocab decks" decision for why
    this lives here rather than a background job (this app has none).
    """
    result = await db.execute(
        select(Card).where(Card.deck_id == deck_id, Card.state == CardState.SUSPENDED)
    )
    suspended_cards = list(result.scalars().all())
    if not suspended_cards:
        return

    for card in suspended_cards:
        vocabulary_item = await db.get(VocabularyItem, card.vocabulary_item_id)
        course = await db.get(Course, vocabulary_item.course_id)
        target_language = await db.get(Language, course.target_language_id)
        gate = target_language.grammar_config.get("vocab_deck", {}).get("production_gate", {})

        recognition_result = await db.execute(
            select(Card).where(
                Card.vocabulary_item_id == card.vocabulary_item_id,
                Card.direction == CardDirection.TARGET_TO_BASE,
            )
        )
        recognition = recognition_result.scalar_one_or_none()
        if recognition is None:
            continue

        unlocked = False
        min_reviews = gate.get("min_successful_recognition_reviews")
        if min_reviews is not None:
            count_result = await db.execute(
                select(func.count(ReviewLog.id)).where(
                    ReviewLog.card_id == recognition.id, ReviewLog.rating != ReviewRating.AGAIN
                )
            )
            if count_result.scalar_one() >= min_reviews:
                unlocked = True

        min_days = gate.get("min_days_since_note_added")
        if not unlocked and min_days is not None:
            note_age_days = (now - vocabulary_item.created_at).total_seconds() / 86400
            if note_age_days >= min_days:
                unlocked = True

        if unlocked:
            card.state = CardState.NEW


async def _count_new_cards_shown_today(db: AsyncSession, deck_id: uuid.UUID, now: datetime) -> int:
    """A NEW card's *first* review produces a ReviewLog row with
    `state_before == CardState.NEW` (see fsrs_engine.py's `apply_review`)
    -- reusing that instead of a new counter table. "Today" is a UTC
    calendar day, consistent with the rest of this backend's UTC-only
    design; a review made right around UTC midnight resets the cap at a
    not-perfectly-local-intuitive time, acceptable for a single-user app.
    """
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    result = await db.execute(
        select(func.count(ReviewLog.id))
        .join(Card, Card.id == ReviewLog.card_id)
        .where(
            Card.deck_id == deck_id,
            ReviewLog.state_before == CardState.NEW,
            ReviewLog.reviewed_at >= today_start,
        )
    )
    return result.scalar_one()


# Registered above /{card_id}: both are 2-segment paths under /cards, and
# route templates are matched in declaration order -- if /{card_id} came
# first, a request for /cards/due would be captured by it with
# card_id="due" (a UUID-parse 422) instead of reaching this handler.
@router.get("/due", response_model=list[CardRead])
async def list_due_cards(
    deck_id: uuid.UUID,
    new_limit: int | None = Query(None, ge=0),
    due_limit: int = Query(100, ge=1),
    db: AsyncSession = Depends(get_db),
) -> list[Card]:
    deck = await get_or_404(db, Deck, deck_id)

    now = datetime.now(UTC)
    await _unlock_eligible_production_cards(db, deck_id, now)
    # Without this commit, the SUSPENDED -> NEW state flips above are only
    # visible for the rest of *this* request -- a GET request's session
    # (see app/database.py's get_db) closes without auto-committing, so an
    # uncommitted unlock silently reverts on the very next /due call
    # (found live: a card that unlocked in one request showed SUSPENDED
    # again on the next).
    await db.commit()

    due_result = await db.execute(
        select(Card)
        .options(selectinload(Card.vocabulary_item))
        .where(
            Card.deck_id == deck_id,
            # Explicit "reviewable" states rather than `!= NEW`, now that
            # SUSPENDED also isn't NEW but must never appear here either.
            Card.state.in_([CardState.LEARNING, CardState.REVIEW, CardState.RELEARNING]),
            Card.due_at <= now,
        )
        .order_by(Card.due_at)
        .limit(due_limit)
    )
    due_cards = list(due_result.scalars().all())

    effective_new_limit = (
        new_limit
        if new_limit is not None
        else (deck.daily_new_card_cap or DEFAULT_DAILY_NEW_CARD_CAP)
    )
    already_shown_today = await _count_new_cards_shown_today(db, deck_id, now)
    remaining_new_limit = max(0, effective_new_limit - already_shown_today)

    new_result = await db.execute(
        select(Card)
        .options(selectinload(Card.vocabulary_item))
        .where(Card.deck_id == deck_id, Card.state == CardState.NEW)
        .order_by(Card.created_at)
        .limit(remaining_new_limit)
    )
    new_cards = list(new_result.scalars().all())

    return due_cards + new_cards


@router.get("/{card_id}", response_model=CardRead)
async def get_card(card_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Card:
    result = await db.execute(
        select(Card).options(selectinload(Card.vocabulary_item)).where(Card.id == card_id)
    )
    card = result.scalar_one_or_none()
    if card is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Card not found")
    return card


@router.patch("/{card_id}", response_model=CardRead)
async def update_card(
    card_id: uuid.UUID, payload: CardUpdate, db: AsyncSession = Depends(get_db)
) -> Card:
    card = await get_or_404(db, Card, card_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(card, field, value)
    await db.commit()
    await db.refresh(card, attribute_names=["vocabulary_item"])
    return card


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_card(card_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> None:
    card = await get_or_404(db, Card, card_id)
    await db.delete(card)
    await db.commit()


@router.post("/{card_id}/review", response_model=CardReviewResponse)
async def submit_card_review(
    card_id: uuid.UUID, payload: CardReviewSubmit, db: AsyncSession = Depends(get_db)
) -> CardReviewResponse:
    """Deliberately doesn't follow update_card's `model_dump(exclude_unset=True)
    + setattr` pattern: the fields this writes aren't a 1:1 payload mapping,
    they're computed from the single `rating` field by the FSRS engine --
    that computation belongs in the service layer, not a generic loop here.
    """
    card = await get_or_404(db, Card, card_id)

    if card.state == CardState.SUSPENDED:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "This card isn't available for review yet (production gate not met).",
        )

    now = datetime.now(UTC)
    if payload.reviewed_at is not None and payload.reviewed_at > now:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "reviewed_at cannot be in the future")
    reviewed_at = payload.reviewed_at or now
    if card.last_reviewed_at is not None and reviewed_at < card.last_reviewed_at:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "reviewed_at cannot precede the card's previous review",
        )

    outcome = apply_review(card, payload.rating, reviewed_at)

    review_log = ReviewLog(
        card_id=card.id,
        reviewed_at=reviewed_at,
        rating=payload.rating,
        elapsed_days=outcome.elapsed_days,
        scheduled_days=outcome.scheduled_days,
        state_before=outcome.state_before,
    )
    db.add(review_log)
    await db.commit()
    await db.refresh(card, attribute_names=["vocabulary_item"])
    return CardReviewResponse(
        card=CardRead.model_validate(card),
        review_log=ReviewLogRead.model_validate(review_log),
    )
