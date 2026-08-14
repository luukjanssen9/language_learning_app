import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.crud_utils import get_or_404
from app.database import get_db
from app.models.course import Course
from app.models.language import Language
from app.models.reading_passage import ReadingPassage, ReadingPassageAttempt
from app.schemas.reading_passage import (
    ReadingPassageAttemptRead,
    ReadingPassageAttemptSubmit,
    ReadingPassageGenerate,
    ReadingPassageRead,
)
from app.services.known_vocabulary_lookup import get_known_words_for_passage
from app.services.llm import LLMProvider, get_llm_provider
from app.services.reading_comprehension_grading import grade_comprehension_answer
from app.services.reading_passage_generation import generate_reading_passage

router = APIRouter(prefix="/reading-passages", tags=["reading-passages"])


@router.post("", response_model=ReadingPassageRead, status_code=status.HTTP_201_CREATED)
async def create_reading_passage(
    payload: ReadingPassageGenerate,
    db: AsyncSession = Depends(get_db),
    llm: LLMProvider = Depends(get_llm_provider),
) -> ReadingPassage:
    course = await get_or_404(db, Course, payload.course_id)
    target_language = await get_or_404(db, Language, course.target_language_id)
    base_language = await get_or_404(db, Language, course.base_language_id)

    known_words = await get_known_words_for_passage(db, course.id)
    result = await generate_reading_passage(
        llm, target_language.name, base_language.name, known_words
    )

    passage = ReadingPassage(
        course_id=course.id,
        target_text=result.target_text,
        base_text=result.base_text,
        new_vocabulary=[w.model_dump() for w in result.new_vocabulary],
        questions=[q.model_dump() for q in result.questions],
    )
    db.add(passage)
    await db.commit()
    await db.refresh(passage)
    return passage


@router.get("", response_model=list[ReadingPassageRead])
async def list_reading_passages(
    course_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> list[ReadingPassage]:
    query = (
        select(ReadingPassage)
        .where(ReadingPassage.course_id == course_id)
        .order_by(ReadingPassage.created_at.desc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("/{passage_id}/attempt", response_model=ReadingPassageAttemptRead)
async def submit_reading_passage_attempt(
    passage_id: uuid.UUID,
    payload: ReadingPassageAttemptSubmit,
    db: AsyncSession = Depends(get_db),
    llm: LLMProvider = Depends(get_llm_provider),
) -> ReadingPassageAttempt:
    passage = await get_or_404(db, ReadingPassage, passage_id)
    if not (0 <= payload.question_index < len(passage.questions)):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="question_index out of range")

    question = passage.questions[payload.question_index]
    grade = await grade_comprehension_answer(
        llm,
        passage.target_text,
        question["question_text"],
        question["reference_answer"],
        payload.submitted_answer,
    )

    attempt = ReadingPassageAttempt(
        user_id=payload.user_id,
        reading_passage_id=passage.id,
        question_index=payload.question_index,
        submitted_answer=payload.submitted_answer,
        is_correct=grade.is_correct,
        llm_feedback=grade.feedback,
    )
    db.add(attempt)
    await db.commit()
    await db.refresh(attempt)
    return attempt
