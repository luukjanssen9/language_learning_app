import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.user_progress import UserProgressRead


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


class UserExerciseAttemptSubmit(BaseModel):
    """Request body for POST /lesson-exercises/{exercise_id}/attempt."""

    submitted_answer: dict


class LessonExerciseAttemptResponse(BaseModel):
    """Bundles the graded attempt with the skill's updated progress, same
    shape as CardReviewResponse: the caller already has both in memory
    after the same commit, so a client showing "correct!" plus an updated
    mastery bar doesn't need a second round trip.

    `correct_answer` is included unconditionally (not just when wrong) to
    keep this endpoint's contract simple -- callers decide whether/when to
    display it. None for MULTIPLE_CHOICE and FREE_TEXT (see
    exercise_grading.get_correct_answer). Not persisted on
    UserExerciseAttempt itself: it's derived fresh from `prompt` +
    grammar_config at request time, not stored, so it can't go stale if
    grammar_config is ever revised later.
    """

    attempt: UserExerciseAttemptRead
    progress: UserProgressRead
    correct_answer: str | None = None
