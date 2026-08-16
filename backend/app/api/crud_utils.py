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


async def get_owned_or_404[ModelT: Base](
    db: AsyncSession,
    model: type[ModelT],
    obj_id: uuid.UUID,
    user_id: uuid.UUID,
    *,
    owner_attr: str = "user_id",
) -> ModelT:
    """Like `get_or_404`, but also verifies `obj.<owner_attr> == user_id`.

    Raises 403 (not 404) on a real ownership mismatch, but with the same
    404-shaped "not found" detail message as a genuinely missing row --
    deliberately indistinguishable from the outside, so a client can't use
    the error text to tell "doesn't exist" apart from "exists but isn't
    yours" and enumerate real IDs that way.
    """
    obj = await get_or_404(db, model, obj_id)
    if getattr(obj, owner_attr) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f"{model.__name__} not found"
        )
    return obj
