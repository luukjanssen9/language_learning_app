import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class VocabularyItemBase(BaseModel):
    course_id: uuid.UUID
    target_text: str
    base_text: str
    part_of_speech: str | None = None
    attributes: dict = {}


class VocabularyItemCreate(VocabularyItemBase):
    pass


class VocabularyItemUpdate(BaseModel):
    target_text: str | None = None
    base_text: str | None = None
    part_of_speech: str | None = None
    attributes: dict | None = None


class VocabularyItemRead(VocabularyItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
