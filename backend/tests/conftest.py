"""Fixtures assume the schema already exists against DATABASE_URL (run
`alembic upgrade head` first). Each test runs inside a transaction that's rolled back afterward
(via a SAVEPOINT, so code under test can freely call `session.commit()`
without leaving data behind), so there's no separate test database.
"""

import uuid
from collections.abc import AsyncIterator, Awaitable, Callable

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.database import engine, get_db
from app.main import app
from app.models.user import User


@pytest_asyncio.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    connection = await engine.connect()
    transaction = await connection.begin()
    session = AsyncSession(
        bind=connection, expire_on_commit=False, join_transaction_mode="create_savepoint"
    )
    try:
        yield session
    finally:
        await session.close()
        await transaction.rollback()
        await connection.close()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    async def override_get_db() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def login_as(
    db_session: AsyncSession,
) -> Callable[[uuid.UUID | str], Awaitable[None]]:
    """Test-only stand-in for a real Google sign-in session (Phase 8 Slice
    4) -- overrides `get_current_user` to return the given user for every
    request the `client` fixture makes from this point on, same swappable-
    `Depends` pattern already used for `get_llm_provider`/`get_tts_client`/
    `get_google_token_verifier`. Call again with a different user_id to
    switch identity mid-test (every cross-user 403 test does this). No
    explicit cleanup needed -- the `client` fixture's own teardown already
    clears every override, this one included.
    """

    async def _login_as(user_id: uuid.UUID | str) -> None:
        user = await db_session.get(User, uuid.UUID(str(user_id)))
        app.dependency_overrides[get_current_user] = lambda: user

    return _login_as
