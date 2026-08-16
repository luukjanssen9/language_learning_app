"""Integration tests for /courses, through the live API + DB
(`client`/`db_session` fixtures from conftest.py). Course-content CRUD is
shared/global by design (Phase 8 slice 1's decision), so unlike most
other resources these routes take no `current_user` at all -- no
ownership checks to cover here, just the plain CRUD contract, same
convention `test_languages.py` already establishes for the other
shared/global resource.
"""

import uuid

from httpx import AsyncClient


async def _make_languages(client: AsyncClient) -> tuple[str, str]:
    suffix = uuid.uuid4().hex[:6]
    lang_en = (
        await client.post("/api/languages", json={"code": f"en-{suffix}", "name": "English"})
    ).json()
    lang_es = (
        await client.post("/api/languages", json={"code": f"es-{suffix}", "name": "Spanish"})
    ).json()
    return lang_en["id"], lang_es["id"]


async def test_create_and_get_course(client: AsyncClient):
    base_id, target_id = await _make_languages(client)
    suffix = uuid.uuid4().hex[:6]

    create_resp = await client.post(
        "/api/courses",
        json={
            "base_language_id": base_id,
            "target_language_id": target_id,
            "name": "English to Spanish",
            "slug": f"en-es-{suffix}",
        },
    )
    assert create_resp.status_code == 201
    body = create_resp.json()
    assert body["name"] == "English to Spanish"
    assert body["base_language_id"] == base_id
    assert body["target_language_id"] == target_id

    get_resp = await client.get(f"/api/courses/{body['id']}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == body["id"]


async def test_list_courses_includes_created(client: AsyncClient):
    base_id, target_id = await _make_languages(client)
    suffix = uuid.uuid4().hex[:6]
    created = (
        await client.post(
            "/api/courses",
            json={
                "base_language_id": base_id,
                "target_language_id": target_id,
                "name": "Test Course",
                "slug": f"list-test-{suffix}",
            },
        )
    ).json()

    list_resp = await client.get("/api/courses")
    assert list_resp.status_code == 200
    assert created["id"] in [c["id"] for c in list_resp.json()]


async def test_get_course_404(client: AsyncClient):
    resp = await client.get(f"/api/courses/{uuid.uuid4()}")
    assert resp.status_code == 404


async def test_update_and_delete_course(client: AsyncClient):
    base_id, target_id = await _make_languages(client)
    suffix = uuid.uuid4().hex[:6]
    created = (
        await client.post(
            "/api/courses",
            json={
                "base_language_id": base_id,
                "target_language_id": target_id,
                "name": "Original Name",
                "slug": f"update-test-{suffix}",
            },
        )
    ).json()

    patch_resp = await client.patch(f"/api/courses/{created['id']}", json={"name": "New Name"})
    assert patch_resp.status_code == 200
    assert patch_resp.json()["name"] == "New Name"
    # base/target language are the course's identity and stay untouched.
    assert patch_resp.json()["base_language_id"] == base_id

    delete_resp = await client.delete(f"/api/courses/{created['id']}")
    assert delete_resp.status_code == 204
    assert (await client.get(f"/api/courses/{created['id']}")).status_code == 404


async def test_duplicate_course_slug_conflicts(client: AsyncClient):
    base_id, target_id = await _make_languages(client)
    suffix = uuid.uuid4().hex[:6]
    payload = {
        "base_language_id": base_id,
        "target_language_id": target_id,
        "name": "Dup",
        "slug": f"dup-{suffix}",
    }
    await client.post("/api/courses", json=payload)
    resp = await client.post("/api/courses", json={**payload, "name": "Dup2"})
    assert resp.status_code == 409
