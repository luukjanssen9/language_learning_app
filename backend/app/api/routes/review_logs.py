import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.api.crud_utils import get_or_404, get_owned_or_404
from app.database import get_db
from app.models.card import Card
from app.models.deck import Deck
from app.models.review_log import ReviewLog
from app.models.user import User
from app.schemas.review_log import ReviewLogRead

router = APIRouter(prefix="/review-logs", tags=["review-logs"])


@router.get("", response_model=list[ReviewLogRead])
async def list_review_logs(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[ReviewLog]:
    result = await db.execute(
        select(ReviewLog)
        .join(Card, Card.id == ReviewLog.card_id)
        .join(Deck, Deck.id == Card.deck_id)
        .where(Deck.user_id == current_user.id)
        .order_by(ReviewLog.reviewed_at.desc())
    )
    return list(result.scalars().all())


@router.get("/{review_log_id}", response_model=ReviewLogRead)
async def get_review_log(
    review_log_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReviewLog:
    review_log = await get_or_404(db, ReviewLog, review_log_id)
    card = await get_or_404(db, Card, review_log.card_id)
    await get_owned_or_404(db, Deck, card.deck_id, current_user.id)
    return review_log
