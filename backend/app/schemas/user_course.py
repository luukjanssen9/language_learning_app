import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserCourseBase(BaseModel):
    user_id: uuid.UUID
    course_id: uuid.UUID


class UserCourseCreate(UserCourseBase):
    pass


class UserCourseRead(UserCourseBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
