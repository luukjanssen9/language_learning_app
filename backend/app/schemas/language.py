import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import ScriptDirection


class LanguageBase(BaseModel):
    code: str
    name: str
    script_direction: ScriptDirection = ScriptDirection.LTR
    grammar_config: dict = {}


class LanguageCreate(LanguageBase):
    pass


class LanguageUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    script_direction: ScriptDirection | None = None
    grammar_config: dict | None = None


class LanguageRead(LanguageBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
