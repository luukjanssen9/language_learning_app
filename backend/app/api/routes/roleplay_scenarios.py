from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.roleplay import RoleplayScenario
from app.schemas.roleplay import RoleplayScenarioRead

router = APIRouter(prefix="/roleplay-scenarios", tags=["roleplay"])


@router.get("", response_model=list[RoleplayScenarioRead])
async def list_roleplay_scenarios(db: AsyncSession = Depends(get_db)) -> list[RoleplayScenario]:
    result = await db.execute(select(RoleplayScenario).order_by(RoleplayScenario.order_index))
    return list(result.scalars().all())
