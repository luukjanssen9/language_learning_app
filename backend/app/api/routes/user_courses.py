import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.crud_utils import get_or_404
from app.database import get_db
from app.models.user_course import UserCourse
from app.schemas.user_course import UserCourseCreate, UserCourseRead

router = APIRouter(prefix="/user-courses", tags=["user-courses"])


@router.post("", response_model=UserCourseRead, status_code=status.HTTP_201_CREATED)
async def create_user_course(
    payload: UserCourseCreate, db: AsyncSession = Depends(get_db)
) -> UserCourse:
    enrollment = UserCourse(**payload.model_dump())
    db.add(enrollment)
    await db.commit()
    await db.refresh(enrollment)
    return enrollment


@router.get("", response_model=list[UserCourseRead])
async def list_user_courses(db: AsyncSession = Depends(get_db)) -> list[UserCourse]:
    result = await db.execute(select(UserCourse).order_by(UserCourse.created_at))
    return list(result.scalars().all())


@router.get("/{user_course_id}", response_model=UserCourseRead)
async def get_user_course(
    user_course_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> UserCourse:
    return await get_or_404(db, UserCourse, user_course_id)


@router.delete("/{user_course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_course(
    user_course_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> None:
    enrollment = await get_or_404(db, UserCourse, user_course_id)
    await db.delete(enrollment)
    await db.commit()
