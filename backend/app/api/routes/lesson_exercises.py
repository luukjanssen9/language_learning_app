import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.crud_utils import get_or_404
from app.database import get_db
from app.models.lesson_exercise import LessonExercise
from app.schemas.lesson_exercise import (
    LessonExerciseCreate,
    LessonExerciseRead,
    LessonExerciseUpdate,
)

router = APIRouter(prefix="/lesson-exercises", tags=["lesson-exercises"])


@router.post("", response_model=LessonExerciseRead, status_code=status.HTTP_201_CREATED)
async def create_lesson_exercise(
    payload: LessonExerciseCreate, db: AsyncSession = Depends(get_db)
) -> LessonExercise:
    exercise = LessonExercise(**payload.model_dump())
    db.add(exercise)
    await db.commit()
    await db.refresh(exercise)
    return exercise


@router.get("", response_model=list[LessonExerciseRead])
async def list_lesson_exercises(db: AsyncSession = Depends(get_db)) -> list[LessonExercise]:
    result = await db.execute(select(LessonExercise).order_by(LessonExercise.order_index))
    return list(result.scalars().all())


@router.get("/{exercise_id}", response_model=LessonExerciseRead)
async def get_lesson_exercise(
    exercise_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> LessonExercise:
    return await get_or_404(db, LessonExercise, exercise_id)


@router.patch("/{exercise_id}", response_model=LessonExerciseRead)
async def update_lesson_exercise(
    exercise_id: uuid.UUID, payload: LessonExerciseUpdate, db: AsyncSession = Depends(get_db)
) -> LessonExercise:
    exercise = await get_or_404(db, LessonExercise, exercise_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(exercise, field, value)
    await db.commit()
    await db.refresh(exercise)
    return exercise


@router.delete("/{exercise_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lesson_exercise(
    exercise_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> None:
    exercise = await get_or_404(db, LessonExercise, exercise_id)
    await db.delete(exercise)
    await db.commit()
