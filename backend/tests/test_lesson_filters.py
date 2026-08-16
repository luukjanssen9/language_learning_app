import uuid

from httpx import AsyncClient


async def _make_course(client: AsyncClient) -> dict:
    suffix = uuid.uuid4().hex[:6]  # Language.code is capped at String(10)
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
                "slug": f"en-es-filters-{suffix}",
            },
        )
    ).json()
    return course


async def test_list_skills_filters_by_course_id(client: AsyncClient):
    course_a = await _make_course(client)
    course_b = await _make_course(client)
    suffix = uuid.uuid4().hex[:6]
    skill_a = (
        await client.post(
            "/api/skills",
            json={"course_id": course_a["id"], "name": "A", "slug": f"a-{suffix}"},
        )
    ).json()
    await client.post(
        "/api/skills", json={"course_id": course_b["id"], "name": "B", "slug": f"b-{suffix}"}
    )

    resp = await client.get("/api/skills", params={"course_id": course_a["id"]})
    assert resp.status_code == 200
    ids = [s["id"] for s in resp.json()]
    assert ids == [skill_a["id"]]


async def test_list_lesson_exercises_filters_by_skill_id(client: AsyncClient):
    course = await _make_course(client)
    suffix = uuid.uuid4().hex[:6]
    skill_a = (
        await client.post(
            "/api/skills", json={"course_id": course["id"], "name": "A", "slug": f"a-{suffix}"}
        )
    ).json()
    skill_b = (
        await client.post(
            "/api/skills", json={"course_id": course["id"], "name": "B", "slug": f"b-{suffix}"}
        )
    ).json()
    exercise_a = (
        await client.post(
            "/api/lesson-exercises",
            json={
                "skill_id": skill_a["id"],
                "exercise_type": "multiple_choice",
                "prompt": {"question": "Q", "options": ["x", "y"], "correct_index": 0},
            },
        )
    ).json()
    await client.post(
        "/api/lesson-exercises",
        json={
            "skill_id": skill_b["id"],
            "exercise_type": "multiple_choice",
            "prompt": {"question": "Q", "options": ["x", "y"], "correct_index": 0},
        },
    )

    resp = await client.get("/api/lesson-exercises", params={"skill_id": skill_a["id"]})
    assert resp.status_code == 200
    ids = [e["id"] for e in resp.json()]
    assert ids == [exercise_a["id"]]


async def test_list_user_progress_is_scoped_to_the_current_user(client: AsyncClient, login_as):
    course = await _make_course(client)
    suffix = uuid.uuid4().hex[:6]
    skill = (
        await client.post(
            "/api/skills",
            json={"course_id": course["id"], "name": "Skill", "slug": f"skill-{suffix}"},
        )
    ).json()
    exercise = (
        await client.post(
            "/api/lesson-exercises",
            json={
                "skill_id": skill["id"],
                "exercise_type": "multiple_choice",
                "prompt": {"question": "Q", "options": ["x", "y"], "correct_index": 0},
            },
        )
    ).json()
    user_a = (
        await client.post(
            "/api/users", json={"email": f"pa-{suffix}@example.com", "display_name": "A"}
        )
    ).json()
    user_b = (
        await client.post(
            "/api/users", json={"email": f"pb-{suffix}@example.com", "display_name": "B"}
        )
    ).json()

    await login_as(user_a["id"])
    await client.post(
        f"/api/lesson-exercises/{exercise['id']}/attempt",
        json={"submitted_answer": {"selected_index": 0}},
    )
    await login_as(user_b["id"])
    await client.post(
        f"/api/lesson-exercises/{exercise['id']}/attempt",
        json={"submitted_answer": {"selected_index": 0}},
    )

    await login_as(user_a["id"])
    resp = await client.get("/api/user-progress")
    assert resp.status_code == 200
    user_ids = {p["user_id"] for p in resp.json()}
    assert user_ids == {user_a["id"]}
