"""Unit tests for `RateLimiter` (app/api/rate_limit.py) plus one
integration test confirming a wired route actually 429s once exceeded.
`now` is passed explicitly throughout rather than relying on real
`time.sleep` for the window-expiry case -- deterministic, and avoids the
class of wall-clock-relative flake already documented in PLAN.md's Known
Issues.
"""

import uuid

import pytest
from fastapi import HTTPException
from httpx import AsyncClient

from app.api.rate_limit import RateLimiter
from app.main import app
from app.services.journal_correction import JournalCorrectionResult
from app.services.llm import get_llm_provider


def test_allows_calls_up_to_the_limit():
    limiter = RateLimiter(max_calls=3, window_seconds=60)
    user_id = uuid.uuid4()
    limiter.check(user_id, now=0.0)
    limiter.check(user_id, now=0.0)
    limiter.check(user_id, now=0.0)


def test_raises_429_once_the_limit_is_exceeded():
    limiter = RateLimiter(max_calls=2, window_seconds=60)
    user_id = uuid.uuid4()
    limiter.check(user_id, now=0.0)
    limiter.check(user_id, now=0.0)

    with pytest.raises(HTTPException) as exc_info:
        limiter.check(user_id, now=0.0)
    assert exc_info.value.status_code == 429


def test_different_users_have_independent_budgets():
    limiter = RateLimiter(max_calls=1, window_seconds=60)
    user_a = uuid.uuid4()
    user_b = uuid.uuid4()
    limiter.check(user_a, now=0.0)
    limiter.check(user_b, now=0.0)  # would raise if budgets were shared


def test_calls_outside_the_window_do_not_count_against_the_limit():
    limiter = RateLimiter(max_calls=2, window_seconds=60)
    user_id = uuid.uuid4()
    limiter.check(user_id, now=0.0)
    limiter.check(user_id, now=10.0)
    # 61s after the first call -- it has aged out of the 60s window, so
    # only the second call (at t=10) still counts and this is allowed.
    limiter.check(user_id, now=61.0)


def test_raises_again_once_still_within_window_calls_hit_the_limit():
    limiter = RateLimiter(max_calls=2, window_seconds=60)
    user_id = uuid.uuid4()
    limiter.check(user_id, now=0.0)
    limiter.check(user_id, now=10.0)

    with pytest.raises(HTTPException) as exc_info:
        limiter.check(user_id, now=20.0)  # both prior calls still in-window
    assert exc_info.value.status_code == 429


class FakeLLMProvider:
    async def generate_structured(self, prompt, response_model, model_tier="fast"):
        return JournalCorrectionResult(
            corrected_text="ok",
            overall_feedback="ok",
            corrections=[],
            vocabulary_suggestions=[],
        )


async def _make_course(client: AsyncClient, login_as) -> dict:
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
                "slug": f"en-es-ratelimit-{suffix}",
            },
        )
    ).json()
    user = (
        await client.post(
            "/api/users",
            json={"email": f"ratelimit-{suffix}@example.com", "display_name": "Rate Limit Test"},
        )
    ).json()
    await login_as(user["id"])
    return course


async def test_journal_entry_endpoint_429s_once_its_budget_is_exhausted(
    client: AsyncClient, login_as
):
    from app.api.rate_limit import journal_correction_limiter

    course = await _make_course(client, login_as)
    app.dependency_overrides[get_llm_provider] = lambda: FakeLLMProvider()

    for _ in range(journal_correction_limiter.max_calls):
        resp = await client.post(
            "/api/journal-entries",
            json={"course_id": course["id"], "text": "Hola."},
        )
        assert resp.status_code == 201, resp.text

    resp = await client.post(
        "/api/journal-entries",
        json={"course_id": course["id"], "text": "Hola de nuevo."},
    )
    assert resp.status_code == 429
