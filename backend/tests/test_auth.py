"""Tests for Google sign-in and session tokens. `test_session_token_*` are
pure unit tests (no DB, no HTTP). The rest are integration tests through
the live API + DB (`client`/`db_session` fixtures from conftest.py) with
the real Google verifier swapped out via the same dependency-override
mechanism `get_llm_provider`/`get_db` already use -- no real network call
to Google in this suite.
"""

import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.user import User
from app.services.auth import (
    AuthError,
    GoogleIdentity,
    create_session_token,
    decode_session_token,
    get_google_token_verifier,
)


def _fake_verifier(identity: GoogleIdentity) -> Callable[[str], Awaitable[GoogleIdentity]]:
    async def verify(credential: str) -> GoogleIdentity:
        return identity

    return verify


def test_session_token_round_trips():
    user_id = uuid.uuid4()
    token = create_session_token(user_id)
    assert decode_session_token(token) == user_id


def test_decode_session_token_rejects_garbage():
    with pytest.raises(AuthError):
        decode_session_token("not-a-real-token")


async def test_first_ever_login_claims_the_legacy_row_in_place(
    client: AsyncClient, db_session: AsyncSession
):
    # The shared dev DB already has its own real, unclaimed seed user --
    # an explicit, deliberately-ancient created_at (overriding the
    # server_default) guarantees this row is the oldest unclaimed one
    # regardless of what else already exists, without needing to touch
    # (and risk a foreign-key violation deleting) any other row.
    legacy = User(
        email="legacy@example.com",
        display_name="Legacy",
        created_at=datetime(2000, 1, 1, tzinfo=UTC),
    )
    db_session.add(legacy)
    await db_session.flush()
    legacy_id = str(legacy.id)

    identity = GoogleIdentity(sub="google-sub-1", email="real@example.com", name="Real Name")
    app.dependency_overrides[get_google_token_verifier] = lambda: _fake_verifier(identity)

    resp = await client.post("/api/auth/google", json={"credential": "whatever"})

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["id"] == legacy_id  # the same row, not a newly created one
    assert body["email"] == "real@example.com"
    assert body["display_name"] == "Real Name"
    assert "session" in resp.cookies


async def test_returning_login_reuses_the_same_user(client: AsyncClient, db_session: AsyncSession):
    identity = GoogleIdentity(sub="google-sub-2", email="a@example.com", name="A")
    app.dependency_overrides[get_google_token_verifier] = lambda: _fake_verifier(identity)

    first = await client.post("/api/auth/google", json={"credential": "x"})
    second = await client.post("/api/auth/google", json={"credential": "y"})

    assert first.json()["id"] == second.json()["id"]


async def test_second_distinct_account_after_claim_creates_a_new_user(
    client: AsyncClient, db_session: AsyncSession
):
    # Explicit ancient created_at, same reasoning as the claim test above --
    # guarantees this row (not the dev DB's real seed user) is the one the
    # first login below claims.
    legacy = User(
        email="legacy2@example.com",
        display_name="Legacy2",
        created_at=datetime(2000, 1, 1, tzinfo=UTC),
    )
    db_session.add(legacy)
    await db_session.flush()

    first_identity = GoogleIdentity(sub="sub-a", email="a@example.com", name="A")
    app.dependency_overrides[get_google_token_verifier] = lambda: _fake_verifier(first_identity)
    first_resp = await client.post("/api/auth/google", json={"credential": "x"})

    second_identity = GoogleIdentity(sub="sub-b", email="b@example.com", name="B")
    app.dependency_overrides[get_google_token_verifier] = lambda: _fake_verifier(second_identity)
    second_resp = await client.post("/api/auth/google", json={"credential": "y"})

    assert first_resp.json()["id"] != second_resp.json()["id"]
    assert second_resp.json()["email"] == "b@example.com"


async def test_me_requires_a_valid_session(client: AsyncClient, db_session: AsyncSession):
    resp = await client.get("/api/auth/me")

    assert resp.status_code == 401


async def test_me_returns_the_signed_in_user(client: AsyncClient, db_session: AsyncSession):
    identity = GoogleIdentity(sub="sub-me", email="me@example.com", name="Me")
    app.dependency_overrides[get_google_token_verifier] = lambda: _fake_verifier(identity)
    await client.post("/api/auth/google", json={"credential": "x"})

    resp = await client.get("/api/auth/me")

    assert resp.status_code == 200
    assert resp.json()["email"] == "me@example.com"


async def test_logout_clears_the_session(client: AsyncClient, db_session: AsyncSession):
    identity = GoogleIdentity(sub="sub-logout", email="logout@example.com", name="Logout")
    app.dependency_overrides[get_google_token_verifier] = lambda: _fake_verifier(identity)
    await client.post("/api/auth/google", json={"credential": "x"})

    logout_resp = await client.post("/api/auth/logout")
    me_resp = await client.get("/api/auth/me")

    assert logout_resp.status_code == 204
    assert me_resp.status_code == 401
