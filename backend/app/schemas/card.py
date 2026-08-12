import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import CardDirection, CardState


class CardBase(BaseModel):
    deck_id: uuid.UUID
    vocabulary_item_id: uuid.UUID | None = None
    front_override: str | None = None
    back_override: str | None = None
    direction: CardDirection = CardDirection.TARGET_TO_BASE


class CardCreate(CardBase):
    pass


class CardUpdate(BaseModel):
    front_override: str | None = None
    back_override: str | None = None
    direction: CardDirection | None = None


class CardRead(CardBase):
    """FSRS scheduling fields are read-only here — they're written by the
    review-submission endpoint (Phase 2), not this basic CRUD surface.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    state: CardState
    stability: float | None
    difficulty: float | None
    due_at: datetime | None
    reps: int
    lapses: int
    last_reviewed_at: datetime | None
