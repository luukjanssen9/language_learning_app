import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.crud_utils import get_or_404
from app.database import get_db
from app.models.language import Language
from app.schemas.language import LanguageCreate, LanguageRead, LanguageUpdate

router = APIRouter(prefix="/languages", tags=["languages"])


@router.post("", response_model=LanguageRead, status_code=status.HTTP_201_CREATED)
async def create_language(
    payload: LanguageCreate, db: AsyncSession = Depends(get_db)
) -> Language:
    language = Language(**payload.model_dump())
    db.add(language)
    await db.commit()
    await db.refresh(language)
    return language


@router.get("", response_model=list[LanguageRead])
async def list_languages(db: AsyncSession = Depends(get_db)) -> list[Language]:
    result = await db.execute(select(Language).order_by(Language.name))
    return list(result.scalars().all())


@router.get("/{language_id}", response_model=LanguageRead)
async def get_language(language_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Language:
    return await get_or_404(db, Language, language_id)


@router.patch("/{language_id}", response_model=LanguageRead)
async def update_language(
    language_id: uuid.UUID, payload: LanguageUpdate, db: AsyncSession = Depends(get_db)
) -> Language:
    language = await get_or_404(db, Language, language_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(language, field, value)
    await db.commit()
    await db.refresh(language)
    return language


@router.delete("/{language_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_language(language_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> None:
    language = await get_or_404(db, Language, language_id)
    await db.delete(language)
    await db.commit()
