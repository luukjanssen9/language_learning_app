import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.api.crud_utils import get_owned_or_404
from app.database import get_db
from app.models.user import User
from app.models.user_exercise_attempt import UserExerciseAttempt
from app.schemas.user_exercise_attempt import UserExerciseAttemptRead

router = APIRouter(prefix="/user-exercise-attempts", tags=["user-exercise-attempts"])


@router.get("", response_model=list[UserExerciseAttemptRead])
async def list_user_exercise_attempts(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[UserExerciseAttempt]:
    result = await db.execute(
        select(UserExerciseAttempt)
        .where(UserExerciseAttempt.user_id == current_user.id)
        .order_by(UserExerciseAttempt.attempted_at.desc())
    )
    return list(result.scalars().all())


@router.get("/{attempt_id}", response_model=UserExerciseAttemptRead)
async def get_user_exercise_attempt(
    attempt_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserExerciseAttempt:
    return await get_owned_or_404(db, UserExerciseAttempt, attempt_id, current_user.id)
