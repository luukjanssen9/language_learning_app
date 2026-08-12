import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base


async def get_or_404[ModelT: Base](
    db: AsyncSession, model: type[ModelT], obj_id: uuid.UUID
) -> ModelT:
    obj = await db.get(model, obj_id)
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"{model.__name__} not found"
        )
    return obj
