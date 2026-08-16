import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.api.crud_utils import get_or_404
from app.database import get_db
from app.models.course import Course
from app.models.enums import ExerciseType
from app.models.language import Language
from app.models.lesson_exercise import LessonExercise
from app.models.skill import Skill
from app.models.user import User
from app.models.user_exercise_attempt import UserExerciseAttempt
from app.models.user_progress import UserProgress
from app.schemas.lesson_exercise import (
    LessonExerciseCreate,
    LessonExerciseRead,
    LessonExerciseUpdate,
)
from app.schemas.user_exercise_attempt import (
    LessonExerciseAttemptResponse,
    UserExerciseAttemptRead,
    UserExerciseAttemptSubmit,
)
from app.schemas.user_progress import UserProgressRead
from app.services.exercise_grading import get_correct_answer, grade_attempt
from app.services.free_text_grading import grade_free_text_attempt
from app.services.llm import LLMProvider, get_llm_provider

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
async def list_lesson_exercises(
    skill_id: uuid.UUID | None = None, db: AsyncSession = Depends(get_db)
) -> list[LessonExercise]:
    query = select(LessonExercise).order_by(LessonExercise.order_index)
    if skill_id is not None:
        query = query.where(LessonExercise.skill_id == skill_id)
    result = await db.execute(query)
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


@router.post("/{exercise_id}/attempt", response_model=LessonExerciseAttemptResponse)
async def submit_lesson_exercise_attempt(
    exercise_id: uuid.UUID,
    payload: UserExerciseAttemptSubmit,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    llm: LLMProvider = Depends(get_llm_provider),
) -> LessonExerciseAttemptResponse:
    """Grades the answer, logs the attempt, and upserts the skill's
    `UserProgress` -- same overall shape as `POST /cards/{id}/review`
    (look up the entity, compute an outcome via a service function,
    persist, return entity + effect).
    """
    exercise = await get_or_404(db, LessonExercise, exercise_id)

    # grammar_config is only needed to grade CONJUGATION exercises, and
    # language names only to grade FREE_TEXT ones -- skip the extra
    # lookups for the (much more common) other exercise types.
    grammar_config: dict | None = None
    llm_feedback: str | None = None
    if exercise.exercise_type == ExerciseType.CONJUGATION:
        skill = await get_or_404(db, Skill, exercise.skill_id)
        course = await get_or_404(db, Course, skill.course_id)
        target_language = await get_or_404(db, Language, course.target_language_id)
        grammar_config = target_language.grammar_config

    if exercise.exercise_type == ExerciseType.FREE_TEXT:
        skill = await get_or_404(db, Skill, exercise.skill_id)
        course = await get_or_404(db, Course, skill.course_id)
        target_language = await get_or_404(db, Language, course.target_language_id)
        base_language = await get_or_404(db, Language, course.base_language_id)
        result = await grade_free_text_attempt(
            llm,
            target_language.name,
            base_language.name,
            exercise.prompt,
            payload.submitted_answer.get("text", ""),
        )
        is_correct = result.is_correct
        llm_feedback = result.feedback
    else:
        is_correct = grade_attempt(exercise, payload.submitted_answer, grammar_config)
    correct_answer = get_correct_answer(exercise, grammar_config)

    attempt = UserExerciseAttempt(
        user_id=current_user.id,
        exercise_id=exercise.id,
        submitted_answer=payload.submitted_answer,
        is_correct=is_correct,
        llm_feedback=llm_feedback,
    )
    db.add(attempt)

    progress_result = await db.execute(
        select(UserProgress).where(
            UserProgress.user_id == current_user.id,
            UserProgress.skill_id == exercise.skill_id,
        )
    )
    progress = progress_result.scalar_one_or_none()
    if progress is None:
        # times_attempted/times_correct's `default=0` is applied at
        # INSERT time, not on construction (same as Card.reps/lapses in
        # fsrs_engine.py) -- set explicitly since we increment below
        # before this row is ever flushed.
        progress = UserProgress(
            user_id=current_user.id,
            skill_id=exercise.skill_id,
            times_attempted=0,
            times_correct=0,
        )
        db.add(progress)

    progress.times_attempted += 1
    if is_correct:
        progress.times_correct += 1
    progress.last_practiced_at = datetime.now(UTC)
    # Plain accuracy ratio, kept deliberately simple per PLAN.md's
    # minimal-gamification decision -- not a smoothed/weighted score.
    progress.mastery_level = progress.times_correct / progress.times_attempted

    await db.commit()
    await db.refresh(attempt)
    await db.refresh(progress)

    return LessonExerciseAttemptResponse(
        attempt=UserExerciseAttemptRead.model_validate(attempt),
        progress=UserProgressRead.model_validate(progress),
        correct_answer=correct_answer,
    )
