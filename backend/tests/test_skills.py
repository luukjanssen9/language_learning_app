"""Integration tests for /skills, through the live API + DB
(`client`/`db_session` fixtures from conftest.py). Course-content CRUD is
shared/global by design (Phase 8 slice 1's decision) -- no ownership
checks to cover here, just the plain CRUD contract. Filter-by-course_id
coverage already lives in test_lesson_filters.py; this file covers the
rest of the CRUD lifecycle that had none.
"""

import uuid

from httpx import AsyncClient


async def _make_course(client: AsyncClient) -> str:
    suffix = uuid.uuid4().hex[:6]
    lang_en = (
        await client.post("/api/languages", json={"code": f"en-{suffix}", "name": "English"})
    ).json()
    lang_es = (
        await client.post("/api/languages", json={"code": f"es-{suffix}", "name": "Spanish"})
    ).json()
    course = (
        await client.post(
            "/api/courses",
            json={
                "base_language_id": lang_en["id"],
                "target_language_id": lang_es["id"],
                "name": "English to Spanish",
                "slug": f"en-es-skills-{suffix}",
            },
        )
    ).json()
    return course["id"]


async def test_create_and_get_skill(client: AsyncClient):
    course_id = await _make_course(client)
    suffix = uuid.uuid4().hex[:6]

    create_resp = await client.post(
        "/api/skills",
        json={"course_id": course_id, "name": "Greetings", "slug": f"greetings-{suffix}"},
    )
    assert create_resp.status_code == 201
    body = create_resp.json()
    assert body["name"] == "Greetings"
    assert body["course_id"] == course_id
    assert body["order_index"] == 0

    get_resp = await client.get(f"/api/skills/{body['id']}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == body["id"]


async def test_get_skill_404(client: AsyncClient):
    resp = await client.get(f"/api/skills/{uuid.uuid4()}")
    assert resp.status_code == 404


async def test_update_and_delete_skill(client: AsyncClient):
    course_id = await _make_course(client)
    suffix = uuid.uuid4().hex[:6]
    created = (
        await client.post(
            "/api/skills",
            json={"course_id": course_id, "name": "Original", "slug": f"orig-{suffix}"},
        )
    ).json()

    patch_resp = await client.patch(
        f"/api/skills/{created['id']}", json={"name": "Renamed", "order_index": 3}
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["name"] == "Renamed"
    assert patch_resp.json()["order_index"] == 3

    delete_resp = await client.delete(f"/api/skills/{created['id']}")
    assert delete_resp.status_code == 204
    assert (await client.get(f"/api/skills/{created['id']}")).status_code == 404
