import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SkillBase(BaseModel):
    course_id: uuid.UUID
    name: str
    slug: str
    order_index: int = 0
    prerequisite_skill_id: uuid.UUID | None = None
    specialty_module: str | None = None
    intro_content: dict | None = None


class SkillCreate(SkillBase):
    pass


class SkillUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    order_index: int | None = None
    prerequisite_skill_id: uuid.UUID | None = None
    specialty_module: str | None = None
    intro_content: dict | None = None


class SkillRead(SkillBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
