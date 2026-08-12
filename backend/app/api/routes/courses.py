import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.crud_utils import get_or_404
from app.database import get_db
from app.models.course import Course
from app.schemas.course import CourseCreate, CourseRead, CourseUpdate

router = APIRouter(prefix="/courses", tags=["courses"])


@router.post("", response_model=CourseRead, status_code=status.HTTP_201_CREATED)
async def create_course(payload: CourseCreate, db: AsyncSession = Depends(get_db)) -> Course:
    course = Course(**payload.model_dump())
    db.add(course)
    await db.commit()
    await db.refresh(course)
    return course


@router.get("", response_model=list[CourseRead])
async def list_courses(db: AsyncSession = Depends(get_db)) -> list[Course]:
    result = await db.execute(select(Course).order_by(Course.name))
    return list(result.scalars().all())


@router.get("/{course_id}", response_model=CourseRead)
async def get_course(course_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Course:
    return await get_or_404(db, Course, course_id)


@router.patch("/{course_id}", response_model=CourseRead)
async def update_course(
    course_id: uuid.UUID, payload: CourseUpdate, db: AsyncSession = Depends(get_db)
) -> Course:
    course = await get_or_404(db, Course, course_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(course, field, value)
    await db.commit()
    await db.refresh(course)
    return course


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(course_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> None:
    course = await get_or_404(db, Course, course_id)
    await db.delete(course)
    await db.commit()
