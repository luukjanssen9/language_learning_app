import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import KnownVocabularySource


class KnownVocabularyItemCreate(BaseModel):
    course_id: uuid.UUID
    target_text: str


class KnownVocabularyBulkCreate(BaseModel):
    course_id: uuid.UUID
    target_texts: list[str]


class KnownVocabularyItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    course_id: uuid.UUID
    target_text: str
    source: KnownVocabularySource
    created_at: datetime


class KnownVocabularyPromote(BaseModel):
    deck_id: uuid.UUID


class KnownVocabularyBulkCreateResponse(BaseModel):
    inserted_count: int


class FullKnownWordSetResponse(BaseModel):
    """The complete, normalized known-word set for a course -- see
    `get_full_known_word_set` (app/services/known_vocabulary_lookup.py).
    """

    words: list[str]
