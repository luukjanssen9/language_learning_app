import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import ExerciseType


class LessonExerciseBase(BaseModel):
    skill_id: uuid.UUID
    exercise_type: ExerciseType
    prompt: dict
    order_index: int = 0
    specialty_module: str | None = None


class LessonExerciseCreate(LessonExerciseBase):
    pass


class LessonExerciseUpdate(BaseModel):
    exercise_type: ExerciseType | None = None
    prompt: dict | None = None
    order_index: int | None = None
    specialty_module: str | None = None


class LessonExerciseRead(LessonExerciseBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
