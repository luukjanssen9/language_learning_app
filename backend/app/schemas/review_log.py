import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import CardState, ReviewRating


class ReviewLogRead(BaseModel):
    """Read-only: rows are written by the review-submission endpoint that
    lands with the FSRS engine in Phase 2, not by direct CRUD.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    card_id: uuid.UUID
    reviewed_at: datetime
    rating: ReviewRating
    elapsed_days: float | None
    scheduled_days: float | None
    state_before: CardState | None
