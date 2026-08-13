import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.crud_utils import get_or_404
from app.database import get_db
from app.models.card import Card
from app.models.deck import Deck
from app.models.enums import CardState
from app.models.review_log import ReviewLog
from app.schemas.card import (
    CardCreate,
    CardRead,
    CardReviewResponse,
    CardReviewSubmit,
    CardUpdate,
)
from app.schemas.review_log import ReviewLogRead
from app.services.fsrs_engine import apply_review

router = APIRouter(prefix="/cards", tags=["cards"])


@router.post("", response_model=CardRead, status_code=status.HTTP_201_CREATED)
async def create_card(payload: CardCreate, db: AsyncSession = Depends(get_db)) -> Card:
    card = Card(**payload.model_dump())
    db.add(card)
    await db.commit()
    await db.refresh(card)
    return card


@router.get("", response_model=list[CardRead])
async def list_cards(db: AsyncSession = Depends(get_db)) -> list[Card]:
    result = await db.execute(select(Card).order_by(Card.created_at))
    return list(result.scalars().all())


# Registered above /{card_id}: both are 2-segment paths under /cards, and
# route templates are matched in declaration order -- if /{card_id} came
# first, a request for /cards/due would be captured by it with
# card_id="due" (a UUID-parse 422) instead of reaching this handler.
@router.get("/due", response_model=list[CardRead])
async def list_due_cards(
    deck_id: uuid.UUID,
    new_limit: int = Query(20, ge=0),
    due_limit: int = Query(100, ge=1),
    db: AsyncSession = Depends(get_db),
) -> list[Card]:
    await get_or_404(db, Deck, deck_id)

    now = datetime.now(UTC)
    due_result = await db.execute(
        select(Card)
        .where(Card.deck_id == deck_id, Card.state != CardState.NEW, Card.due_at <= now)
        .order_by(Card.due_at)
        .limit(due_limit)
    )
    due_cards = list(due_result.scalars().all())

    new_result = await db.execute(
        select(Card)
        .where(Card.deck_id == deck_id, Card.state == CardState.NEW)
        .order_by(Card.created_at)
        .limit(new_limit)
    )
    new_cards = list(new_result.scalars().all())

    return due_cards + new_cards


@router.get("/{card_id}", response_model=CardRead)
async def get_card(card_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Card:
    return await get_or_404(db, Card, card_id)


@router.patch("/{card_id}", response_model=CardRead)
async def update_card(
    card_id: uuid.UUID, payload: CardUpdate, db: AsyncSession = Depends(get_db)
) -> Card:
    card = await get_or_404(db, Card, card_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(card, field, value)
    await db.commit()
    await db.refresh(card)
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
    # No db.refresh() here: every field on `card` was set by our own Python
    # code above (not a server_default), and review_log's id comes from
    # UUIDPkMixin's client-side `default=uuid.uuid4`, not a DB-assigned
    # value -- unlike create_card/update_card, nothing in this response is
    # only known after a round trip.
    return CardReviewResponse(
        card=CardRead.model_validate(card),
        review_log=ReviewLogRead.model_validate(review_log),
    )
