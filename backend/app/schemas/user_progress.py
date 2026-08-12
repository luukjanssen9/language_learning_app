import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserProgressRead(BaseModel):
    """Read-only: rows are written by lesson-practice endpoints landing in
    Phase 4, not by direct CRUD.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    skill_id: uuid.UUID
    mastery_level: float
    last_practiced_at: datetime | None
    times_correct: int
    times_attempted: int
    streak_count: int
    created_at: datetime
