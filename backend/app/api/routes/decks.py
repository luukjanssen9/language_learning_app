import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.crud_utils import get_or_404
from app.database import get_db
from app.models.deck import Deck
from app.schemas.deck import DeckCreate, DeckRead, DeckUpdate

router = APIRouter(prefix="/decks", tags=["decks"])


@router.post("", response_model=DeckRead, status_code=status.HTTP_201_CREATED)
async def create_deck(payload: DeckCreate, db: AsyncSession = Depends(get_db)) -> Deck:
    deck = Deck(**payload.model_dump())
    db.add(deck)
    await db.commit()
    await db.refresh(deck)
    return deck


@router.get("", response_model=list[DeckRead])
async def list_decks(db: AsyncSession = Depends(get_db)) -> list[Deck]:
    result = await db.execute(select(Deck).order_by(Deck.name))
    return list(result.scalars().all())


@router.get("/{deck_id}", response_model=DeckRead)
async def get_deck(deck_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Deck:
    return await get_or_404(db, Deck, deck_id)


@router.patch("/{deck_id}", response_model=DeckRead)
async def update_deck(
    deck_id: uuid.UUID, payload: DeckUpdate, db: AsyncSession = Depends(get_db)
) -> Deck:
    deck = await get_or_404(db, Deck, deck_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(deck, field, value)
    await db.commit()
    await db.refresh(deck)
    return deck


@router.delete("/{deck_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deck(deck_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> None:
    deck = await get_or_404(db, Deck, deck_id)
    await db.delete(deck)
    await db.commit()
