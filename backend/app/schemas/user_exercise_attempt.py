import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserExerciseAttemptRead(BaseModel):
    """Read-only: rows are written by the exercise-submission/grading
    endpoint landing in Phase 4/5, not by direct CRUD.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    exercise_id: uuid.UUID
    submitted_answer: dict
    is_correct: bool | None
    llm_feedback: str | None
    attempted_at: datetime
