"""Google Sign-In verification and this app's own session tokens.

The Google-verification piece is the "one module owns the third-party
library" boundary -- same convention as `app/services/llm/gemini.py` for
`google-genai`, `app/services/fsrs_engine.py` for `fsrs` -- and is exposed
as a swappable FastAPI dependency (`get_google_token_verifier`) so tests
never make a real network call to Google, the same pattern
`get_llm_provider`/`get_tts_client` already use for their own third-party
calls.

Session tokens are a plain HS256 JWT signed with `settings.secret_key`
(already existed, already earmarked "for later phases" before real auth
existed) -- no session table, no refresh-token complexity, appropriate for
a single-tenant-per-login personal app.
"""

import asyncio
import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta

import jwt
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from pydantic import BaseModel

from app.config import settings

SESSION_COOKIE_NAME = "session"
SESSION_TTL = timedelta(days=30)
_JWT_ALGORITHM = "HS256"


class AuthError(Exception):
    """Raised when a Google credential or session token fails verification.
    Callers (routes) are expected to translate this into a 401.
    """


class GoogleIdentity(BaseModel):
    sub: str
    email: str
    name: str


GoogleTokenVerifier = Callable[[str], Awaitable[GoogleIdentity]]


async def _verify_google_id_token(credential: str) -> GoogleIdentity:
    """`verify_oauth2_token` is a blocking call (it does a synchronous HTTP
    fetch of Google's public keys under the hood) -- run it off the event
    loop via `asyncio.to_thread` rather than block it, same async
    discipline as every other I/O call in this codebase.
    """
    try:
        claims = await asyncio.to_thread(
            google_id_token.verify_oauth2_token,
            credential,
            google_requests.Request(),
            settings.google_oauth_client_id,
        )
    except ValueError as exc:
        raise AuthError(f"Invalid Google credential: {exc}") from exc
    return GoogleIdentity(
        sub=claims["sub"], email=claims["email"], name=claims.get("name", claims["email"])
    )


def get_google_token_verifier() -> GoogleTokenVerifier:
    return _verify_google_id_token


def create_session_token(user_id: uuid.UUID) -> str:
    payload = {"sub": str(user_id), "exp": datetime.now(UTC) + SESSION_TTL}
    return jwt.encode(payload, settings.secret_key, algorithm=_JWT_ALGORITHM)


def decode_session_token(token: str) -> uuid.UUID:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[_JWT_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise AuthError(f"Invalid session token: {exc}") from exc
    return uuid.UUID(payload["sub"])
