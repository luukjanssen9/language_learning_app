import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.auth import get_current_user
from app.api.crud_utils import get_or_404, get_owned_or_404
from app.api.rate_limit import card_generation_limiter
from app.database import get_db
from app.models.card import Card
from app.models.course import Course
from app.models.deck import DEFAULT_DAILY_NEW_CARD_CAP, Deck
from app.models.enums import CardDirection, CardState, ReviewRating
from app.models.language import Language
from app.models.review_log import ReviewLog
from app.models.user import User
from app.models.vocabulary import VocabularyItem
from app.schemas.card import (
    CardCreate,
    CardGenerate,
    CardQuickAdd,
    CardQuickAddResponse,
    CardRead,
    CardReviewResponse,
    CardReviewSubmit,
    CardUpdate,
)
from app.schemas.review_log import ReviewLogRead
from app.schemas.vocabulary import VocabularyItemRead
from app.services.card_generation import generate_card_from_word
from app.services.fsrs_engine import apply_review
from app.services.llm import LLMProvider, get_llm_provider
from app.services.note_cards import get_or_create_vocabulary_item_and_cards

router = APIRouter(prefix="/cards", tags=["cards"])


@router.post("", response_model=CardRead, status_code=status.HTTP_201_CREATED)
async def create_card(
    payload: CardCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Card:
    await get_owned_or_404(db, Deck, payload.deck_id, current_user.id)
    card = Card(**payload.model_dump())
    db.add(card)
    await db.commit()
    await db.refresh(card, attribute_names=["vocabulary_item"])
    return card


@router.post("/quick-add", response_model=CardQuickAddResponse, status_code=status.HTTP_201_CREATED)
async def quick_add_card(
    payload: CardQuickAdd,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
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
    deck = await get_owned_or_404(db, Deck, payload.deck_id, current_user.id)
    course = await get_or_404(db, Course, deck.course_id)
    target_language = await get_or_404(db, Language, course.target_language_id)

    vocabulary_item, cards = await get_or_create_vocabulary_item_and_cards(
        db,
        deck,
        target_language,
        target_text=payload.target_text,
        base_text=payload.base_text,
        part_of_speech=payload.part_of_speech,
        source=payload.source,
        example_sentence=payload.example_sentence,
        example_sentence_translation=payload.example_sentence_translation,
        tags=payload.tags,
        attributes=payload.attributes,
    )

    await db.commit()
    await db.refresh(vocabulary_item)
    for card in cards:
        await db.refresh(card, attribute_names=["vocabulary_item"])

    return CardQuickAddResponse(
        vocabulary_item=VocabularyItemRead.model_validate(vocabulary_item),
        cards=[CardRead.model_validate(card) for card in cards],
    )


@router.post("/generate", response_model=CardQuickAddResponse, status_code=status.HTTP_201_CREATED)
async def generate_card(
    payload: CardGenerate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    llm: LLMProvider = Depends(get_llm_provider),
) -> CardQuickAddResponse:
    """The "type a word, get an AI-generated flashcard" button on a deck's
    page: translates `payload.base_text` (a word in the deck's course's
    base language) into the target language via one LLM call
    (app/services/card_generation.py), then reuses the same idempotent
    resolve-or-create note logic `POST /cards/quick-add` uses -- so
    generating a word that's already a note in this course (or already
    has a card in this deck) behaves the same way quick-add does, rather
    than duplicating it.
    """
    card_generation_limiter.check(current_user.id)

    deck = await get_owned_or_404(db, Deck, payload.deck_id, current_user.id)
    course = await get_or_404(db, Course, deck.course_id)
    target_language = await get_or_404(db, Language, course.target_language_id)
    base_language = await get_or_404(db, Language, course.base_language_id)

    vocab_deck_config = target_language.grammar_config.get("vocab_deck", {})
    transliteration_label = (
        vocab_deck_config.get("transliteration_label")
        if vocab_deck_config.get("needs_transliteration")
        else None
    )

    generated = await generate_card_from_word(
        llm, target_language.name, base_language.name, payload.base_text, transliteration_label
    )

    attributes = {}
    if generated.transliteration:
        attributes["transliteration"] = generated.transliteration
    if generated.example_sentence_transliteration:
        attributes["example_sentence_transliteration"] = generated.example_sentence_transliteration

    vocabulary_item, cards = await get_or_create_vocabulary_item_and_cards(
        db,
        deck,
        target_language,
        target_text=generated.target_text,
        base_text=payload.base_text,
        part_of_speech=generated.part_of_speech,
        source="AI-generated",
        example_sentence=generated.example_sentence,
        example_sentence_translation=generated.example_sentence_translation,
        attributes=attributes,
    )

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
    deck_id: uuid.UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Card]:
    query = select(Card).options(selectinload(Card.vocabulary_item)).order_by(Card.created_at)
    if deck_id is not None:
        await get_owned_or_404(db, Deck, deck_id, current_user.id)
        query = query.where(Card.deck_id == deck_id)
    else:
        # No deck_id -- every card across every one of this user's own
        # decks, not literally every card in the database.
        query = query.join(Deck, Deck.id == Card.deck_id).where(Deck.user_id == current_user.id)
    result = await db.execute(query)
    return list(result.scalars().all())


async def _unlock_eligible_production_cards(db: AsyncSession, deck: Deck, now: datetime) -> None:
    """Flips a SUSPENDED production card to NEW once its sibling
    recognition card's production gate is met -- see
    `app/services/note_cards.py`'s module docstring for the config shape
    and PLAN.md's 2026-08-14 "Anki-style vocab decks" decision for why
    this lives here rather than a background job (this app has none).

    Batches every lookup instead of doing it per suspended card: every
    card in `deck` shares the same deck -> course -> target_language, so
    that lookup happens once regardless of how many cards are suspended,
    and vocabulary items / recognition cards / review counts are each
    fetched in one `IN (...)` query rather than one query per card --
    found during the Phase 8 performance review, where a deck with many
    still-gated production cards meant O(n) round trips on every `/due`
    request.
    """
    result = await db.execute(
        select(Card).where(Card.deck_id == deck.id, Card.state == CardState.SUSPENDED)
    )
    suspended_cards = list(result.scalars().all())
    if not suspended_cards:
        return

    course = await db.get(Course, deck.course_id)
    target_language = await db.get(Language, course.target_language_id)
    gate = target_language.grammar_config.get("vocab_deck", {}).get("production_gate", {})
    min_reviews = gate.get("min_successful_recognition_reviews")
    min_days = gate.get("min_days_since_note_added")
    if min_reviews is None and min_days is None:
        return

    vocabulary_item_ids = [card.vocabulary_item_id for card in suspended_cards]
    vocab_result = await db.execute(
        select(VocabularyItem).where(VocabularyItem.id.in_(vocabulary_item_ids))
    )
    vocabulary_items_by_id = {item.id: item for item in vocab_result.scalars()}

    recognition_result = await db.execute(
        select(Card).where(
            Card.vocabulary_item_id.in_(vocabulary_item_ids),
            Card.direction == CardDirection.TARGET_TO_BASE,
        )
    )
    recognition_by_vocab_id = {c.vocabulary_item_id: c for c in recognition_result.scalars()}

    review_counts: dict[uuid.UUID, int] = {}
    if min_reviews is not None:
        recognition_ids = [c.id for c in recognition_by_vocab_id.values()]
        if recognition_ids:
            count_result = await db.execute(
                select(ReviewLog.card_id, func.count(ReviewLog.id))
                .where(
                    ReviewLog.card_id.in_(recognition_ids),
                    ReviewLog.rating != ReviewRating.AGAIN,
                )
                .group_by(ReviewLog.card_id)
            )
            review_counts = dict(count_result.all())

    for card in suspended_cards:
        recognition = recognition_by_vocab_id.get(card.vocabulary_item_id)
        if recognition is None:
            continue

        unlocked = False
        if min_reviews is not None and review_counts.get(recognition.id, 0) >= min_reviews:
            unlocked = True

        if not unlocked and min_days is not None:
            vocabulary_item = vocabulary_items_by_id[card.vocabulary_item_id]
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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Card]:
    deck = await get_owned_or_404(db, Deck, deck_id, current_user.id)

    now = datetime.now(UTC)
    await _unlock_eligible_production_cards(db, deck, now)
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
async def get_card(
    card_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Card:
    result = await db.execute(
        select(Card).options(selectinload(Card.vocabulary_item)).where(Card.id == card_id)
    )
    card = result.scalar_one_or_none()
    if card is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Card not found")
    await get_owned_or_404(db, Deck, card.deck_id, current_user.id)
    return card


@router.patch("/{card_id}", response_model=CardRead)
async def update_card(
    card_id: uuid.UUID,
    payload: CardUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Card:
    card = await get_or_404(db, Card, card_id)
    await get_owned_or_404(db, Deck, card.deck_id, current_user.id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(card, field, value)
    await db.commit()
    await db.refresh(card, attribute_names=["vocabulary_item"])
    return card


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_card(
    card_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    card = await get_or_404(db, Card, card_id)
    await get_owned_or_404(db, Deck, card.deck_id, current_user.id)
    await db.delete(card)
    await db.commit()


@router.post("/{card_id}/review", response_model=CardReviewResponse)
async def submit_card_review(
    card_id: uuid.UUID,
    payload: CardReviewSubmit,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CardReviewResponse:
    """Deliberately doesn't follow update_card's `model_dump(exclude_unset=True)
    + setattr` pattern: the fields this writes aren't a 1:1 payload mapping,
    they're computed from the single `rating` field by the FSRS engine --
    that computation belongs in the service layer, not a generic loop here.
    """
    card = await get_or_404(db, Card, card_id)
    await get_owned_or_404(db, Deck, card.deck_id, current_user.id)

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
