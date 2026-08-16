import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.api.crud_utils import get_or_404
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


def _check_self(user_id: uuid.UUID, current_user: User) -> None:
    """No admin/multi-tenant concept in this app -- a signed-in user can
    only ever look up, edit, or delete their own row, never anyone else's.
    Same 404-shaped 403 detail as get_owned_or_404, for the same
    ID-enumeration-safety reason.
    """
    if user_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="User not found")


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserCreate, db: AsyncSession = Depends(get_db)) -> User:
    user = User(**payload.model_dump())
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    _check_self(user_id, current_user)
    return await get_or_404(db, User, user_id)


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    _check_self(user_id, current_user)
    user = await get_or_404(db, User, user_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    _check_self(user_id, current_user)
    user = await get_or_404(db, User, user_id)
    await db.delete(user)
    await db.commit()
