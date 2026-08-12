import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.crud_utils import get_or_404
from app.database import get_db
from app.models.card import Card
from app.schemas.card import CardCreate, CardRead, CardUpdate

router = APIRouter(prefix="/cards", tags=["cards"])


@router.post("", response_model=CardRead, status_code=status.HTTP_201_CREATED)
async def create_card(payload: CardCreate, db: AsyncSession = Depends(get_db)) -> Card:
    card = Card(**payload.model_dump())
    db.add(card)
    await db.commit()
    await db.refresh(card)
    return card


@router.get("", response_model=list[CardRead])
async def list_cards(db: AsyncSession = Depends(get_db)) -> list[Card]:
    result = await db.execute(select(Card).order_by(Card.created_at))
    return list(result.scalars().all())


@router.get("/{card_id}", response_model=CardRead)
async def get_card(card_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Card:
    return await get_or_404(db, Card, card_id)


@router.patch("/{card_id}", response_model=CardRead)
async def update_card(
    card_id: uuid.UUID, payload: CardUpdate, db: AsyncSession = Depends(get_db)
) -> Card:
    card = await get_or_404(db, Card, card_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(card, field, value)
    await db.commit()
    await db.refresh(card)
    return card


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_card(card_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> None:
    card = await get_or_404(db, Card, card_id)
    await db.delete(card)
    await db.commit()
