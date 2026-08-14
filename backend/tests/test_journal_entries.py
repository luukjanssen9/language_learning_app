"""Integration tests for GET/POST /journal-entries, through the live
API + DB (`client`/`db_session` fixtures from conftest.py). The real
Google Gemini LLM provider is swapped out via the same FastAPI
dependency-override mechanism already used for `get_tts_client`/
`get_llm_provider` elsewhere (see test_tts.py, test_lesson_exercise_attempt.py).
"""

import uuid
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.journal_entry import JournalEntry
from app.services.journal_correction import (
    Correction,
    JournalCorrectionResult,
    VocabSuggestion,
)
from app.services.llm import get_llm_provider


class FakeLLMProvider:
    def __init__(self, result: JournalCorrectionResult) -> None:
        self.result = result

    async def generate_structured(self, prompt, response_model, model_tier="fast"):
        return self.result


async def _make_course(client: AsyncClient) -> dict:
    """Builds Language(x2) -> Course -> User via HTTP. Returns the course
    dict with `_user_id` stashed on it.
    """
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
                "slug": f"en-es-journal-{suffix}",
            },
        )
    ).json()
    user = (
        await client.post(
            "/api/users",
            json={"email": f"journal-{suffix}@example.com", "display_name": "Journal Test"},
        )
    ).json()
    course["_user_id"] = user["id"]
    return course


def _canned_result() -> JournalCorrectionResult:
    return JournalCorrectionResult(
        corrected_text="Ayer fui al mercado.",
        overall_feedback="Good effort, one tense slip.",
        corrections=[
            Correction(
                original="ayer voy",
                corrected="ayer fui",
                explanation="Past events use the preterite.",
            )
        ],
        vocabulary_suggestions=[
            VocabSuggestion(
                target_text="el mercado",
                base_text="the market",
                example_sentence="Ayer fui al mercado.",
            )
        ],
    )


async def test_submit_journal_entry_persists_correction(client: AsyncClient):
    course = await _make_course(client)
    app.dependency_overrides[get_llm_provider] = lambda: FakeLLMProvider(_canned_result())

    resp = await client.post(
        "/api/journal-entries",
        json={
            "user_id": course["_user_id"],
            "course_id": course["id"],
            "text": "Ayer voy al mercado.",
        },
    )

    assert resp.status_code == 201
    body = resp.json()
    assert body["submitted_text"] == "Ayer voy al mercado."
    assert body["corrected_text"] == "Ayer fui al mercado."
    assert body["overall_feedback"] == "Good effort, one tense slip."
    assert body["corrections"] == [
        {
            "original": "ayer voy",
            "corrected": "ayer fui",
            "explanation": "Past events use the preterite.",
        }
    ]
    assert body["vocabulary_suggestions"] == [
        {
            "target_text": "el mercado",
            "base_text": "the market",
            "example_sentence": "Ayer fui al mercado.",
        }
    ]


def _entry(*, user_id, course_id, text: str, created_at: datetime) -> JournalEntry:
    result = _canned_result()
    return JournalEntry(
        user_id=user_id,
        course_id=course_id,
        submitted_text=text,
        corrected_text=result.corrected_text,
        overall_feedback=result.overall_feedback,
        corrections=[c.model_dump() for c in result.corrections],
        vocabulary_suggestions=[v.model_dump() for v in result.vocabulary_suggestions],
        created_at=created_at,
    )


async def test_list_journal_entries_returns_newest_first_scoped_to_course(
    client: AsyncClient, db_session: AsyncSession
):
    course = await _make_course(client)
    other_course = await _make_course(client)
    user_id = course["_user_id"]

    # Inserted directly (not via POST) with explicit, distinct timestamps --
    # Postgres's now()/CURRENT_TIMESTAMP is transaction-start-time-stable,
    # and this whole test runs inside one transaction (see conftest.py), so
    # two POSTs in quick succession would tie on created_at and make
    # "newest first" unverifiable here even though it's real in production
    # (separate requests get separate transactions there).
    now = datetime.now(UTC)
    db_session.add(
        _entry(user_id=user_id, course_id=course["id"], text="Entry one.", created_at=now)
    )
    db_session.add(
        _entry(
            user_id=user_id,
            course_id=course["id"],
            text="Entry two.",
            created_at=now + timedelta(seconds=1),
        )
    )
    # Different course entirely -- must not show up in the course-scoped list.
    db_session.add(
        _entry(
            user_id=other_course["_user_id"],
            course_id=other_course["id"],
            text="Other course entry.",
            created_at=now + timedelta(seconds=2),
        )
    )
    await db_session.commit()

    resp = await client.get(
        "/api/journal-entries", params={"user_id": user_id, "course_id": course["id"]}
    )

    assert resp.status_code == 200
    body = resp.json()
    assert [e["submitted_text"] for e in body] == ["Entry two.", "Entry one."]
