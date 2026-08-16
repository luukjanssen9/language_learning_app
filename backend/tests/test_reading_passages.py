"""Integration tests for the reading-passages endpoints, through the live
API + DB (`client`/`db_session` fixtures from conftest.py). The real
Gemini provider is swapped out via the same dependency-override mechanism
`get_db` uses.
"""

import uuid
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.reading_passage import ReadingPassage
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


def _canned_passage() -> ReadingPassageResult:
    return ReadingPassageResult(
        target_text="Ana va al mercado. Compra fruta fresca.",
        base_text="Ana goes to the market. She buys fresh fruit.",
        new_vocabulary=[NewVocabularyWordResult(target_text="fresca", base_text="fresh")],
        questions=[
            QuestionResult(question_text="¿A dónde va Ana?", reference_answer="Al mercado"),
            QuestionResult(question_text="¿Qué compra?", reference_answer="Fruta fresca"),
        ],
    )


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
                "slug": f"en-es-passages-{suffix}",
            },
        )
    ).json()
    user = (
        await client.post(
            "/api/users",
            json={"email": f"passages-{suffix}@example.com", "display_name": "Passages Test"},
        )
    ).json()
    return {**course, "_user_id": user["id"]}


async def test_create_reading_passage_persists_and_excludes_reference_answer(
    client: AsyncClient,
):
    course = await _make_course(client)
    app.dependency_overrides[get_llm_provider] = lambda: FakeLLMProvider(_canned_passage())

    resp = await client.post(
        "/api/reading-passages",
        json={"course_id": course["id"], "user_id": course["_user_id"]},
    )

    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["target_text"] == "Ana va al mercado. Compra fruta fresca."
    assert body["new_vocabulary"] == [{"target_text": "fresca", "base_text": "fresh"}]
    assert body["questions"] == [
        {"question_text": "¿A dónde va Ana?"},
        {"question_text": "¿Qué compra?"},
    ]
    assert "reference_answer" not in body["questions"][0]


async def test_list_reading_passages_is_course_scoped(client: AsyncClient):
    course_a = await _make_course(client)
    course_b = await _make_course(client)
    app.dependency_overrides[get_llm_provider] = lambda: FakeLLMProvider(_canned_passage())

    await client.post(
        "/api/reading-passages",
        json={"course_id": course_a["id"], "user_id": course_a["_user_id"]},
    )
    await client.post(
        "/api/reading-passages",
        json={"course_id": course_b["id"], "user_id": course_b["_user_id"]},
    )

    resp = await client.get(
        "/api/reading-passages",
        params={"course_id": course_a["id"], "user_id": course_a["_user_id"]},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1


async def test_list_reading_passages_excludes_other_users_in_same_course(client: AsyncClient):
    course = await _make_course(client)
    other_user = (
        await client.post(
            "/api/users",
            json={"email": f"other-{uuid.uuid4().hex[:6]}@example.com", "display_name": "Other"},
        )
    ).json()
    app.dependency_overrides[get_llm_provider] = lambda: FakeLLMProvider(_canned_passage())

    await client.post(
        "/api/reading-passages",
        json={"course_id": course["id"], "user_id": course["_user_id"]},
    )
    await client.post(
        "/api/reading-passages",
        json={"course_id": course["id"], "user_id": other_user["id"]},
    )

    resp = await client.get(
        "/api/reading-passages",
        params={"course_id": course["id"], "user_id": course["_user_id"]},
    )

    assert resp.status_code == 200
    assert len(resp.json()) == 1


async def test_list_reading_passages_orders_most_recent_first(
    client: AsyncClient, db_session: AsyncSession
):
    # Inserted directly via db_session with explicit, distinct timestamps
    # rather than through back-to-back API calls: Postgres's now() is
    # transaction-start-time-stable, and this project's tests run inside
    # one transaction (see conftest.py), so two rows created via the API
    # in the same test can get identical created_at values -- see PLAN.md's
    # 2026-08-14 "Journal correction" entry for the same issue hit there.
    course = await _make_course(client)
    now = datetime.now(UTC)
    older = ReadingPassage(
        course_id=uuid.UUID(course["id"]),
        user_id=uuid.UUID(course["_user_id"]),
        target_text="older",
        base_text="older",
        new_vocabulary=[],
        questions=[],
        created_at=now - timedelta(minutes=5),
    )
    newer = ReadingPassage(
        course_id=uuid.UUID(course["id"]),
        user_id=uuid.UUID(course["_user_id"]),
        target_text="newer",
        base_text="newer",
        new_vocabulary=[],
        questions=[],
        created_at=now,
    )
    db_session.add_all([older, newer])
    await db_session.flush()

    resp = await client.get(
        "/api/reading-passages",
        params={"course_id": course["id"], "user_id": course["_user_id"]},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert [p["target_text"] for p in body] == ["newer", "older"]


async def test_attempt_grades_and_persists(client: AsyncClient):
    course = await _make_course(client)
    app.dependency_overrides[get_llm_provider] = lambda: FakeLLMProvider(_canned_passage())
    passage = (
        await client.post(
            "/api/reading-passages",
            json={"course_id": course["id"], "user_id": course["_user_id"]},
        )
    ).json()

    fake_grade = FakeLLMProvider(ComprehensionGradeResult(is_correct=True, feedback="Correct!"))
    app.dependency_overrides[get_llm_provider] = lambda: fake_grade

    resp = await client.post(
        f"/api/reading-passages/{passage['id']}/attempt",
        json={
            "user_id": course["_user_id"],
            "question_index": 0,
            "submitted_answer": "Al mercado",
        },
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["is_correct"] is True
    assert body["llm_feedback"] == "Correct!"
    assert body["question_index"] == 0
    assert fake_grade.call_count == 1


async def test_attempt_with_out_of_range_question_index_is_400(client: AsyncClient):
    course = await _make_course(client)
    app.dependency_overrides[get_llm_provider] = lambda: FakeLLMProvider(_canned_passage())
    passage = (
        await client.post(
            "/api/reading-passages",
            json={"course_id": course["id"], "user_id": course["_user_id"]},
        )
    ).json()

    resp = await client.post(
        f"/api/reading-passages/{passage['id']}/attempt",
        json={"user_id": course["_user_id"], "question_index": 99, "submitted_answer": "x"},
    )

    assert resp.status_code == 400
