import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class VocabularyItemBase(BaseModel):
    course_id: uuid.UUID
    target_text: str
    base_text: str
    part_of_speech: str | None = None
    attributes: dict = {}
    # Real, sourced content ("where did this word come from") -- distinct
    # from VocabularyExample's LLM-generated practice sentences, see that
    # model's docstring. All optional: lesson-seeded vocab (Greetings,
    # Family, ...) has none of these.
    source: str | None = None
    example_sentence: str | None = None
    example_sentence_translation: str | None = None
    tags: list[str] = []


class VocabularyItemCreate(VocabularyItemBase):
    pass


class VocabularyItemUpdate(BaseModel):
    target_text: str | None = None
    base_text: str | None = None
    part_of_speech: str | None = None
    attributes: dict | None = None
    source: str | None = None
    example_sentence: str | None = None
    example_sentence_translation: str | None = None
    tags: list[str] | None = None


class VocabularyItemRead(VocabularyItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime


class VocabularyExampleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    target_text: str
    base_text: str
    created_at: datetime


class NewVocabularyWord(BaseModel):
    """A bare word + translation, no other metadata -- shared by any
    feature that surfaces "you encountered this new word, want to add it?"
    (reading-passage generation, paste-in unknown-word flagging).
    """

    target_text: str
    base_text: str
