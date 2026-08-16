"""Integration tests for /users, through the live API + DB
(`client`/`db_session` fixtures from conftest.py). `POST /users` is
exercised implicitly by nearly every other test file's setup helper, but
the self-only `GET/PATCH/DELETE /users/{id}` behavior (Phase 8 slice 4's
`_check_self`) had no direct coverage anywhere -- this file closes that
gap.
"""

import uuid

from httpx import AsyncClient


async def _make_user(client: AsyncClient) -> dict:
    suffix = uuid.uuid4().hex[:6]
    return (
        await client.post(
            "/api/users",
            json={"email": f"users-test-{suffix}@example.com", "display_name": "Test User"},
        )
    ).json()


async def test_create_user(client: AsyncClient):
    resp = await client.post(
        "/api/users",
        json={"email": f"create-{uuid.uuid4().hex[:6]}@example.com", "display_name": "New User"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["display_name"] == "New User"
    assert "id" in body


async def test_duplicate_email_conflicts(client: AsyncClient):
    payload = {"email": f"dup-{uuid.uuid4().hex[:6]}@example.com", "display_name": "Dup"}
    await client.post("/api/users", json=payload)
    resp = await client.post("/api/users", json={**payload, "display_name": "Dup2"})
    assert resp.status_code == 409


async def test_get_own_user(client: AsyncClient, login_as):
    user = await _make_user(client)
    await login_as(user["id"])

    resp = await client.get(f"/api/users/{user['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == user["id"]


async def test_get_someone_elses_user_is_403(client: AsyncClient, login_as):
    user_a = await _make_user(client)
    user_b = await _make_user(client)
    await login_as(user_b["id"])

    resp = await client.get(f"/api/users/{user_a['id']}")
    assert resp.status_code == 403


async def test_update_own_user(client: AsyncClient, login_as):
    user = await _make_user(client)
    await login_as(user["id"])

    resp = await client.patch(f"/api/users/{user['id']}", json={"display_name": "Renamed"})
    assert resp.status_code == 200
    assert resp.json()["display_name"] == "Renamed"


async def test_update_someone_elses_user_is_403(client: AsyncClient, login_as):
    user_a = await _make_user(client)
    user_b = await _make_user(client)
    await login_as(user_b["id"])

    resp = await client.patch(f"/api/users/{user_a['id']}", json={"display_name": "Hijacked"})
    assert resp.status_code == 403


async def test_delete_own_user(client: AsyncClient, login_as):
    user = await _make_user(client)
    await login_as(user["id"])

    resp = await client.delete(f"/api/users/{user['id']}")
    assert resp.status_code == 204


async def test_delete_someone_elses_user_is_403(client: AsyncClient, login_as):
    user_a = await _make_user(client)
    user_b = await _make_user(client)
    await login_as(user_b["id"])

    resp = await client.delete(f"/api/users/{user_a['id']}")
    assert resp.status_code == 403


async def test_get_user_by_id_requires_auth(client: AsyncClient):
    user = await _make_user(client)
    resp = await client.get(f"/api/users/{user['id']}")
    assert resp.status_code == 401
