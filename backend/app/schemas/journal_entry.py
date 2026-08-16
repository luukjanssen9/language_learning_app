import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class JournalEntrySubmit(BaseModel):
    """Request body for POST /journal-entries."""

    course_id: uuid.UUID
    text: str


class Correction(BaseModel):
    original: str
    corrected: str
    explanation: str


class VocabSuggestion(BaseModel):
    target_text: str
    base_text: str
    example_sentence: str


class JournalEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    course_id: uuid.UUID
    submitted_text: str
    corrected_text: str
    overall_feedback: str
    corrections: list[Correction]
    vocabulary_suggestions: list[VocabSuggestion]
    created_at: datetime
