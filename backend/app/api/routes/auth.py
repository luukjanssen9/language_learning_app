import uuid

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.auth import GoogleSignIn
from app.schemas.user import UserRead
from app.services.auth import (
    SESSION_COOKIE_NAME,
    SESSION_TTL,
    GoogleTokenVerifier,
    create_session_token,
    get_google_token_verifier,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_session_cookie(response: Response, user_id: uuid.UUID) -> None:
    # samesite="none" requires secure=True (browsers reject the pairing
    # otherwise) -- both flip together off of the same environment check,
    # matching the existing dev-vs-prod pattern in app/database.py.
    is_prod = settings.environment != "development"
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=create_session_token(user_id),
        httponly=True,
        secure=is_prod,
        samesite="none" if is_prod else "lax",
        max_age=int(SESSION_TTL.total_seconds()),
        path="/",
    )


@router.post("/google", response_model=UserRead)
async def sign_in_with_google(
    payload: GoogleSignIn,
    response: Response,
    db: AsyncSession = Depends(get_db),
    verify: GoogleTokenVerifier = Depends(get_google_token_verifier),
) -> User:
    """Verifies the Google credential, then resolves it to a `User` row:

    - An existing `google_sub` match -> that's a returning login.
    - No `google_sub` in the whole table has ever been set (nobody has
      signed in for real yet) -> claim the oldest unclaimed row in place
      (updates its google_sub/email/display_name) rather than creating a
      new one, so every existing user_id-linked row (decks, journal
      entries, conversations, ...) carries over automatically -- see
      PLAN.md's Phase 8 slice 1 decision for why this is "reassign," not
      "migrate data between rows."
    - Otherwise (auth already claimed by someone else, this is a genuinely
      new identity) -> create a new `User`.
    """
    identity = await verify(payload.credential)

    result = await db.execute(select(User).where(User.google_sub == identity.sub))
    user = result.scalar_one_or_none()

    if user is None:
        already_claimed = await db.execute(
            select(User.id).where(User.google_sub.is_not(None)).limit(1)
        )
        if already_claimed.scalar_one_or_none() is None:
            legacy_result = await db.execute(
                select(User).where(User.google_sub.is_(None)).order_by(User.created_at).limit(1)
            )
            user = legacy_result.scalar_one_or_none()

        if user is None:
            user = User(google_sub=identity.sub, email=identity.email, display_name=identity.name)
            db.add(user)
        else:
            user.google_sub = identity.sub
            user.email = identity.email
            user.display_name = identity.name

    await db.commit()
    await db.refresh(user)

    _set_session_cookie(response, user.id)
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")


@router.get("/me", response_model=UserRead)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
