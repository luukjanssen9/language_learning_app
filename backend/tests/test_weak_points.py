"""Integration tests for GET /weak-points, through the live API + DB
(`client`/`db_session` fixtures from conftest.py). Exercises all three
signal queries in `app/services/weak_points.py` plus their thresholds and
course isolation.
"""

import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.card import Card
from app.models.enums import CardDirection
from app.models.lesson_exercise import LessonExerciseVocabulary


async def _make_course(client: AsyncClient, login_as) -> dict:
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
                "slug": f"en-es-weakpoints-{suffix}",
            },
        )
    ).json()
    user = (
        await client.post(
            "/api/users",
            json={"email": f"weakpoints-{suffix}@example.com", "display_name": "Weak Points Test"},
        )
    ).json()
    await login_as(user["id"])
    return {"course_id": course["id"], "user_id": user["id"]}


async def _make_deck(client: AsyncClient, course_id: str) -> str:
    deck = (
        await client.post(
            "/api/decks",
            json={"course_id": course_id, "name": "Weak points deck"},
        )
    ).json()
    return deck["id"]


async def _make_vocab_item(client: AsyncClient, course_id: str, target_text: str) -> str:
    item = (
        await client.post(
            "/api/vocabulary-items",
            json={
                "course_id": course_id,
                "target_text": target_text,
                "base_text": target_text,
            },
        )
    ).json()
    return item["id"]


async def _make_skill(client: AsyncClient, course_id: str, slug: str) -> str:
    skill = (
        await client.post(
            "/api/skills",
            json={"course_id": course_id, "name": slug, "slug": slug},
        )
    ).json()
    return skill["id"]


async def _make_translation_exercise(
    client: AsyncClient, skill_id: str, correct_answer: str
) -> str:
    exercise = (
        await client.post(
            "/api/lesson-exercises",
            json={
                "skill_id": skill_id,
                "exercise_type": "translation",
                "prompt": {"prompt_text": correct_answer, "correct_answer": correct_answer},
            },
        )
    ).json()
    return exercise["id"]


async def _link_exercise_vocab(
    db_session: AsyncSession, exercise_id: str, vocabulary_item_id: str
) -> None:
    db_session.add(
        LessonExerciseVocabulary(
            lesson_exercise_id=uuid.UUID(exercise_id),
            vocabulary_item_id=uuid.UUID(vocabulary_item_id),
        )
    )
    await db_session.flush()


async def _submit_attempt(
    client: AsyncClient, exercise_id: str, *, correct: bool, correct_answer: str
) -> None:
    text = correct_answer if correct else "definitely-wrong"
    resp = await client.post(
        f"/api/lesson-exercises/{exercise_id}/attempt",
        json={"submitted_answer": {"text": text}},
    )
    assert resp.status_code == 200, resp.text


async def test_weak_cards_ranked_by_lapses_and_excludes_zero_lapses(
    client: AsyncClient, db_session: AsyncSession, login_as
):
    ctx = await _make_course(client, login_as)
    deck_id = await _make_deck(client, ctx["course_id"])
    weak_item = await _make_vocab_item(client, ctx["course_id"], "gato")
    fine_item = await _make_vocab_item(client, ctx["course_id"], "perro")

    db_session.add_all(
        [
            Card(
                deck_id=uuid.UUID(deck_id),
                vocabulary_item_id=uuid.UUID(weak_item),
                direction=CardDirection.TARGET_TO_BASE,
                lapses=3,
            ),
            Card(
                deck_id=uuid.UUID(deck_id),
                vocabulary_item_id=uuid.UUID(fine_item),
                direction=CardDirection.TARGET_TO_BASE,
                lapses=0,
            ),
        ]
    )
    await db_session.flush()

    resp = await client.get("/api/weak-points", params={"course_id": ctx["course_id"]})

    assert resp.status_code == 200, resp.text
    weak_cards = resp.json()["weak_cards"]
    assert [c["target_text"] for c in weak_cards] == ["gato"]
    assert weak_cards[0]["lapses"] == 3
    assert weak_cards[0]["deck_id"] == deck_id


async def test_weak_card_without_vocabulary_item_is_excluded(
    client: AsyncClient, db_session: AsyncSession, login_as
):
    ctx = await _make_course(client, login_as)
    deck_id = await _make_deck(client, ctx["course_id"])

    db_session.add(
        Card(
            deck_id=uuid.UUID(deck_id),
            vocabulary_item_id=None,
            front_override="manual front",
            direction=CardDirection.TARGET_TO_BASE,
            lapses=5,
        )
    )
    await db_session.flush()

    resp = await client.get("/api/weak-points", params={"course_id": ctx["course_id"]})

    assert resp.status_code == 200, resp.text
    assert resp.json()["weak_cards"] == []


async def test_weak_lesson_words_respects_min_attempts_and_accuracy_threshold(
    client: AsyncClient, db_session: AsyncSession, login_as
):
    ctx = await _make_course(client, login_as)
    skill_id = await _make_skill(client, ctx["course_id"], "vocab-basics")

    # "malo": 1/2 correct (50% accuracy, 2 attempts) -- should qualify.
    malo_item = await _make_vocab_item(client, ctx["course_id"], "malo")
    malo_exercise = await _make_translation_exercise(client, skill_id, "bad")
    await _link_exercise_vocab(db_session, malo_exercise, malo_item)
    await _submit_attempt(client, malo_exercise, correct=True, correct_answer="bad")
    await _submit_attempt(client, malo_exercise, correct=False, correct_answer="bad")

    # "bien": always correct -- should NOT qualify (accuracy too high).
    bien_item = await _make_vocab_item(client, ctx["course_id"], "bien")
    bien_exercise = await _make_translation_exercise(client, skill_id, "well")
    await _link_exercise_vocab(db_session, bien_exercise, bien_item)
    await _submit_attempt(client, bien_exercise, correct=True, correct_answer="well")
    await _submit_attempt(client, bien_exercise, correct=True, correct_answer="well")

    # "una-vez": wrong, but only 1 attempt -- should NOT qualify (below MIN_ATTEMPTS).
    once_item = await _make_vocab_item(client, ctx["course_id"], "una-vez")
    once_exercise = await _make_translation_exercise(client, skill_id, "once")
    await _link_exercise_vocab(db_session, once_exercise, once_item)
    await _submit_attempt(client, once_exercise, correct=False, correct_answer="once")

    resp = await client.get("/api/weak-points", params={"course_id": ctx["course_id"]})

    assert resp.status_code == 200, resp.text
    weak_words = resp.json()["weak_lesson_words"]
    assert [w["target_text"] for w in weak_words] == ["malo"]
    assert weak_words[0]["times_attempted"] == 2
    assert weak_words[0]["accuracy"] == 0.5
    assert weak_words[0]["skill_id"] == skill_id


async def test_weak_skills_respects_min_attempts_and_mastery_threshold(
    client: AsyncClient, login_as
):
    ctx = await _make_course(client, login_as)

    weak_skill_id = await _make_skill(client, ctx["course_id"], "shaky-skill")
    weak_exercise = await _make_translation_exercise(client, weak_skill_id, "si")
    await _submit_attempt(client, weak_exercise, correct=False, correct_answer="si")
    await _submit_attempt(client, weak_exercise, correct=False, correct_answer="si")

    strong_skill_id = await _make_skill(client, ctx["course_id"], "solid-skill")
    strong_exercise = await _make_translation_exercise(client, strong_skill_id, "no")
    await _submit_attempt(client, strong_exercise, correct=True, correct_answer="no")
    await _submit_attempt(client, strong_exercise, correct=True, correct_answer="no")

    barely_tried_skill_id = await _make_skill(client, ctx["course_id"], "barely-tried")
    barely_tried_exercise = await _make_translation_exercise(client, barely_tried_skill_id, "tal")
    await _submit_attempt(client, barely_tried_exercise, correct=False, correct_answer="tal")

    resp = await client.get("/api/weak-points", params={"course_id": ctx["course_id"]})

    assert resp.status_code == 200, resp.text
    weak_skills = resp.json()["weak_skills"]
    assert [s["skill_id"] for s in weak_skills] == [weak_skill_id]
    assert weak_skills[0]["mastery_level"] == 0.0
    assert weak_skills[0]["times_attempted"] == 2


async def test_second_course_data_does_not_bleed_in(
    client: AsyncClient, db_session: AsyncSession, login_as
):
    ctx_a = await _make_course(client, login_as)
    ctx_b = await _make_course(client, login_as)

    deck_b = await _make_deck(client, ctx_b["course_id"])
    other_item = await _make_vocab_item(client, ctx_b["course_id"], "otro")
    db_session.add(
        Card(
            deck_id=uuid.UUID(deck_b),
            vocabulary_item_id=uuid.UUID(other_item),
            direction=CardDirection.TARGET_TO_BASE,
            lapses=9,
        )
    )
    await db_session.flush()

    await login_as(ctx_a["user_id"])
    resp = await client.get("/api/weak-points", params={"course_id": ctx_a["course_id"]})

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body == {"weak_cards": [], "weak_lesson_words": [], "weak_skills": []}
