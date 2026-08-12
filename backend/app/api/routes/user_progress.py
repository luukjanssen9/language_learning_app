import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.crud_utils import get_or_404
from app.database import get_db
from app.models.user_progress import UserProgress
from app.schemas.user_progress import UserProgressRead

router = APIRouter(prefix="/user-progress", tags=["user-progress"])


@router.get("", response_model=list[UserProgressRead])
async def list_user_progress(db: AsyncSession = Depends(get_db)) -> list[UserProgress]:
    result = await db.execute(select(UserProgress).order_by(UserProgress.last_practiced_at))
    return list(result.scalars().all())


@router.get("/{user_progress_id}", response_model=UserProgressRead)
async def get_user_progress(
    user_progress_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> UserProgress:
    return await get_or_404(db, UserProgress, user_progress_id)
