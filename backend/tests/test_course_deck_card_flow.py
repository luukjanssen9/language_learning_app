import uuid

from httpx import AsyncClient


async def test_full_course_deck_card_flow(client: AsyncClient):
    """Exercises the full FK graph: Language -> Course -> Deck ->
    VocabularyItem -> Card, plus a Skill/LessonExercise off the same course.
    """
    lang_en = (
        await client.post("/api/languages", json={"code": "en-flow", "name": "English"})
    ).json()
    lang_es = (
        await client.post("/api/languages", json={"code": "es-flow", "name": "Spanish"})
    ).json()

    course = (
        await client.post(
            "/api/courses",
            json={
                "base_language_id": lang_en["id"],
                "target_language_id": lang_es["id"],
                "name": "English to Spanish",
                "slug": "en-es-flow",
            },
        )
    ).json()

    user = (
        await client.post(
            "/api/users", json={"email": "flow-test@example.com", "display_name": "Flow Test"}
        )
    ).json()

    deck = (
        await client.post(
            "/api/decks",
            json={"user_id": user["id"], "course_id": course["id"], "name": "Test deck"},
        )
    ).json()

    vocab = (
        await client.post(
            "/api/vocabulary-items",
            json={
                "course_id": course["id"],
                "user_id": user["id"],
                "target_text": "perro",
                "base_text": "dog",
            },
        )
    ).json()

    card_resp = await client.post(
        "/api/cards", json={"deck_id": deck["id"], "vocabulary_item_id": vocab["id"]}
    )
    assert card_resp.status_code == 201
    card = card_resp.json()
    assert card["state"] == "new"
    assert card["reps"] == 0
    assert card["direction"] == "target_to_base"
    assert card["due_at"] is None

    skill = (
        await client.post(
            "/api/skills",
            json={"course_id": course["id"], "name": "Greetings", "slug": "greetings-flow"},
        )
    ).json()

    exercise_resp = await client.post(
        "/api/lesson-exercises",
        json={
            "skill_id": skill["id"],
            "exercise_type": "translation",
            "prompt": {"text": "Translate: dog"},
        },
    )
    assert exercise_resp.status_code == 201
    assert exercise_resp.json()["exercise_type"] == "translation"


async def test_course_with_bad_language_fk_conflicts(client: AsyncClient):
    resp = await client.post(
        "/api/courses",
        json={
            "base_language_id": str(uuid.uuid4()),
            "target_language_id": str(uuid.uuid4()),
            "name": "Bad course",
            "slug": "bad-fk-flow",
        },
    )
    assert resp.status_code == 409
