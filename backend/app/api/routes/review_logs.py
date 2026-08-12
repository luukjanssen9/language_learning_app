import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.crud_utils import get_or_404
from app.database import get_db
from app.models.review_log import ReviewLog
from app.schemas.review_log import ReviewLogRead

router = APIRouter(prefix="/review-logs", tags=["review-logs"])


@router.get("", response_model=list[ReviewLogRead])
async def list_review_logs(db: AsyncSession = Depends(get_db)) -> list[ReviewLog]:
    result = await db.execute(select(ReviewLog).order_by(ReviewLog.reviewed_at.desc()))
    return list(result.scalars().all())


@router.get("/{review_log_id}", response_model=ReviewLogRead)
async def get_review_log(review_log_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> ReviewLog:
    return await get_or_404(db, ReviewLog, review_log_id)
