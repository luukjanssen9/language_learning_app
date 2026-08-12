import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CourseBase(BaseModel):
    base_language_id: uuid.UUID
    target_language_id: uuid.UUID
    name: str
    slug: str


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    """Base/target language are the course's identity and aren't mutable
    here — create a new course instead of repointing one.
    """

    name: str | None = None
    slug: str | None = None


class CourseRead(CourseBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
