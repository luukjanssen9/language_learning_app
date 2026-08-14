import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.crud_utils import get_or_404
from app.database import get_db
from app.models.course import Course
from app.models.language import Language
from app.models.vocabulary import VocabularyItem
from app.models.vocabulary_example import VocabularyExample
from app.schemas.vocabulary import (
    VocabularyExampleRead,
    VocabularyItemCreate,
    VocabularyItemRead,
    VocabularyItemUpdate,
)
from app.services.llm import LLMProvider, get_llm_provider
from app.services.sentence_generation import generate_example_sentences

router = APIRouter(prefix="/vocabulary-items", tags=["vocabulary"])


@router.post("", response_model=VocabularyItemRead, status_code=status.HTTP_201_CREATED)
async def create_vocabulary_item(
    payload: VocabularyItemCreate, db: AsyncSession = Depends(get_db)
) -> VocabularyItem:
    item = VocabularyItem(**payload.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.get("", response_model=list[VocabularyItemRead])
async def list_vocabulary_items(
    course_id: uuid.UUID | None = None, db: AsyncSession = Depends(get_db)
) -> list[VocabularyItem]:
    query = select(VocabularyItem).order_by(VocabularyItem.target_text)
    if course_id is not None:
        query = query.where(VocabularyItem.course_id == course_id)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/{item_id}", response_model=VocabularyItemRead)
async def get_vocabulary_item(
    item_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> VocabularyItem:
    return await get_or_404(db, VocabularyItem, item_id)


@router.patch("/{item_id}", response_model=VocabularyItemRead)
async def update_vocabulary_item(
    item_id: uuid.UUID, payload: VocabularyItemUpdate, db: AsyncSession = Depends(get_db)
) -> VocabularyItem:
    item = await get_or_404(db, VocabularyItem, item_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    await db.commit()
    await db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vocabulary_item(item_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> None:
    item = await get_or_404(db, VocabularyItem, item_id)
    await db.delete(item)
    await db.commit()


@router.get("/{item_id}/examples", response_model=list[VocabularyExampleRead])
async def get_vocabulary_item_examples(
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    llm: LLMProvider = Depends(get_llm_provider),
) -> list[VocabularyExample]:
    """Get-or-generate: returns cached examples if any exist for this word,
    otherwise generates them via the LLM layer and persists the result --
    so a given vocabulary item only ever costs one real LLM call across
    its whole lifetime, not one per page view (see `VocabularyExample`'s
    docstring for why that matters on Gemini's free tier).
    """
    item = await get_or_404(db, VocabularyItem, item_id)

    result = await db.execute(
        select(VocabularyExample).where(VocabularyExample.vocabulary_item_id == item_id)
    )
    existing = list(result.scalars().all())
    if existing:
        return existing

    course = await get_or_404(db, Course, item.course_id)
    target_language = await get_or_404(db, Language, course.target_language_id)
    base_language = await get_or_404(db, Language, course.base_language_id)

    generated = await generate_example_sentences(
        llm,
        target_language_name=target_language.name,
        base_language_name=base_language.name,
        target_text=item.target_text,
        part_of_speech=item.part_of_speech,
    )
    examples = [
        VocabularyExample(
            vocabulary_item_id=item.id,
            target_text=example.target_text,
            base_text=example.base_text,
        )
        for example in generated
    ]
    db.add_all(examples)
    await db.commit()
    for example in examples:
        await db.refresh(example)
    return examples
