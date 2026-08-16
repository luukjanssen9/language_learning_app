import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserCourseBase(BaseModel):
    course_id: uuid.UUID


class UserCourseCreate(UserCourseBase):
    pass


class UserCourseRead(UserCourseBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
