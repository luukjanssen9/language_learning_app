import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.vocabulary import NewVocabularyWord


class ReadingPassageGenerate(BaseModel):
    """Request body for POST /reading-passages."""

    course_id: uuid.UUID


class ReadingPassageQuestion(BaseModel):
    """Client-facing question shape -- deliberately excludes
    `reference_answer`, which stays server-side only (see
    `ReadingPassageRead` below, which reads these off the stored row's
    JSONB but drops that field on the way out).
    """

    question_text: str


class ReadingPassageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    course_id: uuid.UUID
    user_id: uuid.UUID
    target_text: str
    base_text: str
    new_vocabulary: list[NewVocabularyWord]
    questions: list[ReadingPassageQuestion]
    created_at: datetime


class ReadingPassageAttemptSubmit(BaseModel):
    """Request body for POST /reading-passages/{id}/attempt."""

    question_index: int
    submitted_answer: str


class ReadingPassageAttemptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    reading_passage_id: uuid.UUID
    question_index: int
    submitted_answer: str
    is_correct: bool | None
    llm_feedback: str | None
    created_at: datetime
