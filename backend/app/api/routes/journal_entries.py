import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.crud_utils import get_or_404
from app.database import get_db
from app.models.course import Course
from app.models.journal_entry import JournalEntry
from app.models.language import Language
from app.schemas.journal_entry import JournalEntryRead, JournalEntrySubmit
from app.services.journal_correction import correct_journal_entry
from app.services.llm import LLMProvider, get_llm_provider

router = APIRouter(prefix="/journal-entries", tags=["journal-entries"])


@router.post("", response_model=JournalEntryRead, status_code=status.HTTP_201_CREATED)
async def submit_journal_entry(
    payload: JournalEntrySubmit,
    db: AsyncSession = Depends(get_db),
    llm: LLMProvider = Depends(get_llm_provider),
) -> JournalEntry:
    course = await get_or_404(db, Course, payload.course_id)
    target_language = await get_or_404(db, Language, course.target_language_id)
    base_language = await get_or_404(db, Language, course.base_language_id)

    result = await correct_journal_entry(
        llm, target_language.name, base_language.name, payload.text
    )

    entry = JournalEntry(
        user_id=payload.user_id,
        course_id=payload.course_id,
        submitted_text=payload.text,
        corrected_text=result.corrected_text,
        overall_feedback=result.overall_feedback,
        corrections=[c.model_dump() for c in result.corrections],
        vocabulary_suggestions=[v.model_dump() for v in result.vocabulary_suggestions],
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


@router.get("", response_model=list[JournalEntryRead])
async def list_journal_entries(
    user_id: uuid.UUID,
    course_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[JournalEntry]:
    query = (
        select(JournalEntry)
        .where(JournalEntry.user_id == user_id, JournalEntry.course_id == course_id)
        .order_by(JournalEntry.created_at.desc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())
