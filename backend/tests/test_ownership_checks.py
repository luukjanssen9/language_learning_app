"""Integration tests for Phase 8 Slice 3's ownership-check hardening --
routes not already covered by a nearby feature's own test file
(decks, user-courses, review-logs, user-exercise-attempts, user-progress,
vocabulary-item mutation, reading-passage attempts). See PLAN.md's
2026-08-16 Phase 8 Slice 3 decision.
"""

import uuid

from httpx import AsyncClient
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.vocabulary import VocabularyItem
from app.services.llm import get_llm_provider
from app.services.llm.base import ModelTier
from app.services.reading_comprehension_grading import ComprehensionGradeResult
from app.services.reading_passage_generation import (
    NewVocabularyWordResult,
    QuestionResult,
    ReadingPassageResult,
)


class FakeLLMProvider:
    def __init__(self, canned_response: BaseModel) -> None:
        self.canned_response = canned_response
        self.call_count = 0

    async def generate_structured(
        self, prompt: str, response_model: type, model_tier: ModelTier = "fast"
    ) -> BaseModel:
        self.call_count += 1
        return self.canned_response


async def _make_course(client: AsyncClient) -> dict:
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
                "slug": f"en-es-ownership-{suffix}",
            },
        )
    ).json()
    return course


async def _make_user(client: AsyncClient) -> dict:
    suffix = uuid.uuid4().hex[:8]
    return (
        await client.post(
            "/api/users",
            json={"email": f"ownership-{suffix}@example.com", "display_name": "Ownership Test"},
        )
    ).json()


async def _make_deck(client: AsyncClient, course_id: str, user_id: str) -> dict:
    return (
        await client.post(
            "/api/decks",
            json={"user_id": user_id, "course_id": course_id, "name": "Ownership deck"},
        )
    ).json()


# --- decks.py ---


async def test_list_decks_excludes_other_users_decks(client: AsyncClient):
    course = await _make_course(client)
    user_a = await _make_user(client)
    user_b = await _make_user(client)
    deck_a = await _make_deck(client, course["id"], user_a["id"])
    await _make_deck(client, course["id"], user_b["id"])

    resp = await client.get("/api/decks", params={"user_id": user_a["id"]})

    assert resp.status_code == 200
    ids = [d["id"] for d in resp.json()]
    assert ids == [deck_a["id"]]


async def test_get_someone_elses_deck_is_403(client: AsyncClient):
    course = await _make_course(client)
    user_a = await _make_user(client)
    user_b = await _make_user(client)
    deck = await _make_deck(client, course["id"], user_a["id"])

    resp = await client.get(f"/api/decks/{deck['id']}", params={"user_id": user_b["id"]})

    assert resp.status_code == 403


async def test_update_someone_elses_deck_is_403(client: AsyncClient):
    course = await _make_course(client)
    user_a = await _make_user(client)
    user_b = await _make_user(client)
    deck = await _make_deck(client, course["id"], user_a["id"])

    resp = await client.patch(
        f"/api/decks/{deck['id']}", params={"user_id": user_b["id"]}, json={"name": "Hijacked"}
    )

    assert resp.status_code == 403


async def test_delete_someone_elses_deck_is_403(client: AsyncClient):
    course = await _make_course(client)
    user_a = await _make_user(client)
    user_b = await _make_user(client)
    deck = await _make_deck(client, course["id"], user_a["id"])

    resp = await client.delete(f"/api/decks/{deck['id']}", params={"user_id": user_b["id"]})

    assert resp.status_code == 403
    # Confirm it's still there -- a 403 must not have deleted it anyway.
    get_resp = await client.get(f"/api/decks/{deck['id']}", params={"user_id": user_a["id"]})
    assert get_resp.status_code == 200


# --- user_courses.py ---


async def test_list_user_courses_excludes_other_users_enrollments(client: AsyncClient):
    course = await _make_course(client)
    user_a = await _make_user(client)
    user_b = await _make_user(client)
    enrollment_a = (
        await client.post(
            "/api/user-courses", json={"user_id": user_a["id"], "course_id": course["id"]}
        )
    ).json()
    await client.post(
        "/api/user-courses", json={"user_id": user_b["id"], "course_id": course["id"]}
    )

    resp = await client.get("/api/user-courses", params={"user_id": user_a["id"]})

    assert resp.status_code == 200
    ids = [e["id"] for e in resp.json()]
    assert ids == [enrollment_a["id"]]


async def test_get_someone_elses_user_course_is_403(client: AsyncClient):
    course = await _make_course(client)
    user_a = await _make_user(client)
    user_b = await _make_user(client)
    enrollment = (
        await client.post(
            "/api/user-courses", json={"user_id": user_a["id"], "course_id": course["id"]}
        )
    ).json()

    resp = await client.get(
        f"/api/user-courses/{enrollment['id']}", params={"user_id": user_b["id"]}
    )

    assert resp.status_code == 403


async def test_delete_someone_elses_user_course_is_403(client: AsyncClient):
    course = await _make_course(client)
    user_a = await _make_user(client)
    user_b = await _make_user(client)
    enrollment = (
        await client.post(
            "/api/user-courses", json={"user_id": user_a["id"], "course_id": course["id"]}
        )
    ).json()

    resp = await client.delete(
        f"/api/user-courses/{enrollment['id']}", params={"user_id": user_b["id"]}
    )

    assert resp.status_code == 403


# --- review_logs.py (transitive via Card -> Deck) ---


async def test_list_review_logs_excludes_other_users_logs(client: AsyncClient):
    course = await _make_course(client)
    user_a = await _make_user(client)
    user_b = await _make_user(client)
    deck_a = await _make_deck(client, course["id"], user_a["id"])
    deck_b = await _make_deck(client, course["id"], user_b["id"])
    vocab_a = (
        await client.post(
            "/api/vocabulary-items",
            json={
                "course_id": course["id"],
                "user_id": user_a["id"],
                "target_text": "perro",
                "base_text": "dog",
            },
        )
    ).json()
    vocab_b = (
        await client.post(
            "/api/vocabulary-items",
            json={
                "course_id": course["id"],
                "user_id": user_b["id"],
                "target_text": "gato",
                "base_text": "cat",
            },
        )
    ).json()
    card_a = (
        await client.post(
            "/api/cards",
            params={"user_id": user_a["id"]},
            json={"deck_id": deck_a["id"], "vocabulary_item_id": vocab_a["id"]},
        )
    ).json()
    card_b = (
        await client.post(
            "/api/cards",
            params={"user_id": user_b["id"]},
            json={"deck_id": deck_b["id"], "vocabulary_item_id": vocab_b["id"]},
        )
    ).json()
    review_a = (
        await client.post(
            f"/api/cards/{card_a['id']}/review",
            params={"user_id": user_a["id"]},
            json={"rating": "good"},
        )
    ).json()["review_log"]
    await client.post(
        f"/api/cards/{card_b['id']}/review",
        params={"user_id": user_b["id"]},
        json={"rating": "good"},
    )

    resp = await client.get("/api/review-logs", params={"user_id": user_a["id"]})

    assert resp.status_code == 200
    ids = [r["id"] for r in resp.json()]
    assert ids == [review_a["id"]]

    get_resp = await client.get(
        f"/api/review-logs/{review_a['id']}", params={"user_id": user_a["id"]}
    )
    assert get_resp.status_code == 200


async def test_get_someone_elses_review_log_is_403(client: AsyncClient):
    course = await _make_course(client)
    user_a = await _make_user(client)
    user_b = await _make_user(client)
    deck_a = await _make_deck(client, course["id"], user_a["id"])
    vocab_a = (
        await client.post(
            "/api/vocabulary-items",
            json={
                "course_id": course["id"],
                "user_id": user_a["id"],
                "target_text": "perro",
                "base_text": "dog",
            },
        )
    ).json()
    card_a = (
        await client.post(
            "/api/cards",
            params={"user_id": user_a["id"]},
            json={"deck_id": deck_a["id"], "vocabulary_item_id": vocab_a["id"]},
        )
    ).json()
    review_a = (
        await client.post(
            f"/api/cards/{card_a['id']}/review",
            params={"user_id": user_a["id"]},
            json={"rating": "good"},
        )
    ).json()["review_log"]

    resp = await client.get(f"/api/review-logs/{review_a['id']}", params={"user_id": user_b["id"]})

    assert resp.status_code == 403


# --- user_exercise_attempts.py / user_progress.py (via lesson-exercise attempt) ---


async def test_list_and_get_user_exercise_attempts_scoped_by_owner(client: AsyncClient):
    course = await _make_course(client)
    user_a = await _make_user(client)
    user_b = await _make_user(client)
    skill = (
        await client.post(
            "/api/skills",
            json={
                "course_id": course["id"],
                "name": "Greetings",
                "slug": f"g-{uuid.uuid4().hex[:6]}",
            },
        )
    ).json()
    exercise = (
        await client.post(
            "/api/lesson-exercises",
            json={
                "skill_id": skill["id"],
                "exercise_type": "translation",
                "prompt": {"prompt_text": "dog", "correct_answer": "perro"},
            },
        )
    ).json()
    attempt_a = (
        await client.post(
            f"/api/lesson-exercises/{exercise['id']}/attempt",
            json={"user_id": user_a["id"], "submitted_answer": {"text": "perro"}},
        )
    ).json()["attempt"]
    await client.post(
        f"/api/lesson-exercises/{exercise['id']}/attempt",
        json={"user_id": user_b["id"], "submitted_answer": {"text": "perro"}},
    )

    list_resp = await client.get("/api/user-exercise-attempts", params={"user_id": user_a["id"]})
    assert list_resp.status_code == 200
    assert [a["id"] for a in list_resp.json()] == [attempt_a["id"]]

    get_resp = await client.get(
        f"/api/user-exercise-attempts/{attempt_a['id']}", params={"user_id": user_a["id"]}
    )
    assert get_resp.status_code == 200

    forbidden_resp = await client.get(
        f"/api/user-exercise-attempts/{attempt_a['id']}", params={"user_id": user_b["id"]}
    )
    assert forbidden_resp.status_code == 403


async def test_get_someone_elses_user_progress_is_403(client: AsyncClient):
    course = await _make_course(client)
    user_a = await _make_user(client)
    user_b = await _make_user(client)
    skill = (
        await client.post(
            "/api/skills",
            json={"course_id": course["id"], "name": "Family", "slug": f"f-{uuid.uuid4().hex[:6]}"},
        )
    ).json()
    exercise = (
        await client.post(
            "/api/lesson-exercises",
            json={
                "skill_id": skill["id"],
                "exercise_type": "translation",
                "prompt": {"prompt_text": "mother", "correct_answer": "madre"},
            },
        )
    ).json()
    progress = (
        await client.post(
            f"/api/lesson-exercises/{exercise['id']}/attempt",
            json={"user_id": user_a["id"], "submitted_answer": {"text": "madre"}},
        )
    ).json()["progress"]

    resp = await client.get(
        f"/api/user-progress/{progress['id']}", params={"user_id": user_b["id"]}
    )

    assert resp.status_code == 403


# --- vocabulary.py PATCH/DELETE, including the shared-curriculum NULL case ---


async def test_update_someone_elses_vocabulary_item_is_403(client: AsyncClient):
    course = await _make_course(client)
    user_a = await _make_user(client)
    user_b = await _make_user(client)
    item = (
        await client.post(
            "/api/vocabulary-items",
            json={
                "course_id": course["id"],
                "user_id": user_a["id"],
                "target_text": "perro",
                "base_text": "dog",
            },
        )
    ).json()

    resp = await client.patch(
        f"/api/vocabulary-items/{item['id']}",
        params={"user_id": user_b["id"]},
        json={"base_text": "hijacked"},
    )

    assert resp.status_code == 403


async def test_delete_someone_elses_vocabulary_item_is_403(client: AsyncClient):
    course = await _make_course(client)
    user_a = await _make_user(client)
    user_b = await _make_user(client)
    item = (
        await client.post(
            "/api/vocabulary-items",
            json={
                "course_id": course["id"],
                "user_id": user_a["id"],
                "target_text": "perro",
                "base_text": "dog",
            },
        )
    ).json()

    resp = await client.delete(
        f"/api/vocabulary-items/{item['id']}", params={"user_id": user_b["id"]}
    )

    assert resp.status_code == 403


async def test_shared_curriculum_vocabulary_item_cannot_be_mutated_by_anyone(
    client: AsyncClient, db_session: AsyncSession
):
    """A NULL-user_id row (shared curriculum) has no owner -- PATCH/DELETE
    must always 403, even for the user who happens to be able to read it.
    """
    course = await _make_course(client)
    user = await _make_user(client)
    shared_item = VocabularyItem(
        course_id=uuid.UUID(course["id"]),
        user_id=None,
        target_text="hola",
        base_text="hello",
    )
    db_session.add(shared_item)
    await db_session.flush()

    read_resp = await client.get(
        f"/api/vocabulary-items/{shared_item.id}", params={"user_id": user["id"]}
    )
    assert read_resp.status_code == 200

    patch_resp = await client.patch(
        f"/api/vocabulary-items/{shared_item.id}",
        params={"user_id": user["id"]},
        json={"base_text": "hijacked"},
    )
    assert patch_resp.status_code == 403

    delete_resp = await client.delete(
        f"/api/vocabulary-items/{shared_item.id}", params={"user_id": user["id"]}
    )
    assert delete_resp.status_code == 403


async def test_reading_vocabulary_item_owned_by_another_user_is_403(client: AsyncClient):
    course = await _make_course(client)
    user_a = await _make_user(client)
    user_b = await _make_user(client)
    item = (
        await client.post(
            "/api/vocabulary-items",
            json={
                "course_id": course["id"],
                "user_id": user_a["id"],
                "target_text": "perro",
                "base_text": "dog",
            },
        )
    ).json()

    resp = await client.get(f"/api/vocabulary-items/{item['id']}", params={"user_id": user_b["id"]})

    assert resp.status_code == 403


# --- reading_passages.py attempt ---


def _canned_passage() -> ReadingPassageResult:
    return ReadingPassageResult(
        target_text="Ana va al mercado.",
        base_text="Ana goes to the market.",
        new_vocabulary=[NewVocabularyWordResult(target_text="mercado", base_text="market")],
        questions=[QuestionResult(question_text="¿A dónde va Ana?", reference_answer="Al mercado")],
    )


async def test_attempting_someone_elses_reading_passage_is_403(client: AsyncClient):
    course = await _make_course(client)
    user_a = await _make_user(client)
    user_b = await _make_user(client)
    app.dependency_overrides[get_llm_provider] = lambda: FakeLLMProvider(_canned_passage())

    passage = (
        await client.post(
            "/api/reading-passages",
            json={"course_id": course["id"], "user_id": user_a["id"]},
        )
    ).json()

    app.dependency_overrides[get_llm_provider] = lambda: FakeLLMProvider(
        ComprehensionGradeResult(is_correct=True, feedback="Correct!")
    )
    resp = await client.post(
        f"/api/reading-passages/{passage['id']}/attempt",
        json={"user_id": user_b["id"], "question_index": 0, "submitted_answer": "Al mercado"},
    )

    assert resp.status_code == 403
