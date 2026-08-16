import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DeckBase(BaseModel):
    course_id: uuid.UUID
    name: str
    description: str | None = None
    # None means "use the app-wide default" (DEFAULT_DAILY_NEW_CARD_CAP in
    # app/models/deck.py), not "no cap" -- see GET /cards/due.
    daily_new_card_cap: int | None = None


class DeckCreate(DeckBase):
    pass


class DeckUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    daily_new_card_cap: int | None = None


class DeckRead(DeckBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    # Not on DeckCreate -- the owner is always the signed-in user
    # (app/api/auth.py's get_current_user), never a client-supplied value.
    user_id: uuid.UUID
    created_at: datetime
