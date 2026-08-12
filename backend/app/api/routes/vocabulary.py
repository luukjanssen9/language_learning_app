import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.crud_utils import get_or_404
from app.database import get_db
from app.models.vocabulary import VocabularyItem
from app.schemas.vocabulary import VocabularyItemCreate, VocabularyItemRead, VocabularyItemUpdate

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
async def list_vocabulary_items(db: AsyncSession = Depends(get_db)) -> list[VocabularyItem]:
    result = await db.execute(select(VocabularyItem).order_by(VocabularyItem.target_text))
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
