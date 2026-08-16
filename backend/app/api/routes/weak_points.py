import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.weak_points import (
    WeakCardResult,
    WeakLessonWordResult,
    WeakPointsResponse,
    WeakSkillResult,
)
from app.services.weak_points import get_weak_cards, get_weak_lesson_words, get_weak_skills

router = APIRouter(prefix="/weak-points", tags=["weak-points"])


@router.get("", response_model=WeakPointsResponse)
async def get_weak_points(
    course_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WeakPointsResponse:
    weak_cards = await get_weak_cards(db, current_user.id, course_id)
    weak_lesson_words = await get_weak_lesson_words(db, current_user.id, course_id)
    weak_skills = await get_weak_skills(db, current_user.id, course_id)
    return WeakPointsResponse(
        weak_cards=[WeakCardResult(**row) for row in weak_cards],
        weak_lesson_words=[WeakLessonWordResult(**row) for row in weak_lesson_words],
        weak_skills=[WeakSkillResult(**row) for row in weak_skills],
    )
