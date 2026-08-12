import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.crud_utils import get_or_404
from app.database import get_db
from app.models.skill import Skill
from app.schemas.skill import SkillCreate, SkillRead, SkillUpdate

router = APIRouter(prefix="/skills", tags=["skills"])


@router.post("", response_model=SkillRead, status_code=status.HTTP_201_CREATED)
async def create_skill(payload: SkillCreate, db: AsyncSession = Depends(get_db)) -> Skill:
    skill = Skill(**payload.model_dump())
    db.add(skill)
    await db.commit()
    await db.refresh(skill)
    return skill


@router.get("", response_model=list[SkillRead])
async def list_skills(db: AsyncSession = Depends(get_db)) -> list[Skill]:
    result = await db.execute(select(Skill).order_by(Skill.order_index))
    return list(result.scalars().all())


@router.get("/{skill_id}", response_model=SkillRead)
async def get_skill(skill_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Skill:
    return await get_or_404(db, Skill, skill_id)


@router.patch("/{skill_id}", response_model=SkillRead)
async def update_skill(
    skill_id: uuid.UUID, payload: SkillUpdate, db: AsyncSession = Depends(get_db)
) -> Skill:
    skill = await get_or_404(db, Skill, skill_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(skill, field, value)
    await db.commit()
    await db.refresh(skill)
    return skill


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(skill_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> None:
    skill = await get_or_404(db, Skill, skill_id)
    await db.delete(skill)
    await db.commit()
