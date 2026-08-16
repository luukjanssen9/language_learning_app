from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.services.auth import SESSION_COOKIE_NAME, AuthError, decode_session_token


async def get_current_user(
    request: Request, db: AsyncSession = Depends(get_db)
) -> User:
    """Derives the signed-in user from the session cookie -- every route
    that reads/mutates a specific user's data depends on this rather than
    trusting a client-supplied `user_id` (see PLAN.md's Phase 8 slice 4).
    """
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Not signed in")
    try:
        user_id = decode_session_token(token)
    except AuthError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid session") from exc

    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid session")
    return user
