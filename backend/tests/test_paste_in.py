"""Integration tests for the paste-in endpoints, through the live API + DB
(`client`/`db_session` fixtures from conftest.py). The real Gemini
provider is swapped out for /translate-unknown-words via the same
dependency-override mechanism `get_db` uses.
"""

import uuid

from httpx import AsyncClient
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.card import Card
from app.models.enums import CardDirection, CardState
from app.services.llm import get_llm_provider
from app.services.llm.base import ModelTier
from app.services.word_translation import BatchWordTranslation, WordTranslationBatchResult


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
                "slug": f"en-es-pastein-{suffix}",
            },
        )
    ).json()
    return {**course, "_target_language_id": lang_es["id"]}


async def _add_known_word(client: AsyncClient, course_id: str, word: str) -> None:
    resp = await client.post(
        "/api/known-vocabulary", json={"course_id": course_id, "target_text": word}
    )
    assert resp.status_code == 201, resp.text


async def test_analyze_flags_unknown_words_and_reconstructs_text(client: AsyncClient):
    course = await _make_course(client)
    await _add_known_word(client, course["id"], "hola")

    resp = await client.post(
        "/api/paste-in/analyze",
        json={"course_id": course["id"], "text": "Hola, esdrújula amiga."},
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    reconstructed = "".join(s["text"] for s in body["segments"])
    assert reconstructed == "Hola, esdrújula amiga."

    words = {s["text"]: s for s in body["segments"] if s["is_word"]}
    assert words["Hola"]["is_known"] is True  # matches known word, accent/case-insensitive
    assert words["esdrújula"]["is_known"] is False
    assert words["amiga"]["is_known"] is False
    assert set(body["unknown_words"]) == {"esdrújula", "amiga"}


async def test_analyze_counts_a_mastered_card_as_known(
    client: AsyncClient, db_session: AsyncSession
):
    course = await _make_course(client)
    item = (
        await client.post(
            "/api/vocabulary-items",
            json={"course_id": course["id"], "target_text": "perro", "base_text": "dog"},
        )
    ).json()
    deck_user = (
        await client.post(
            "/api/users",
            json={"email": f"{uuid.uuid4().hex[:8]}@example.com", "display_name": "T"},
        )
    ).json()
    deck = (
        await client.post(
            "/api/decks",
            json={"user_id": deck_user["id"], "course_id": course["id"], "name": "D"},
        )
    ).json()
    # A REVIEW-state card has no HTTP path without real FSRS review timing
    # -- inserted directly via db_session, same convention used elsewhere
    # for state that can't be reached through the API alone.
    db_session.add(
        Card(
            deck_id=uuid.UUID(deck["id"]),
            vocabulary_item_id=uuid.UUID(item["id"]),
            direction=CardDirection.TARGET_TO_BASE,
            state=CardState.REVIEW,
        )
    )
    await db_session.flush()

    resp = await client.post(
        "/api/paste-in/analyze", json={"course_id": course["id"], "text": "perro"}
    )

    assert resp.json()["unknown_words"] == []


async def test_analyze_uses_cjk_segmentation_when_configured(client: AsyncClient):
    suffix = uuid.uuid4().hex[:6]
    lang_en = (
        await client.post("/api/languages", json={"code": f"en-{suffix}", "name": "English"})
    ).json()
    lang_zh = (
        await client.post(
            "/api/languages",
            json={
                "code": f"zh-{suffix}",
                "name": "Chinese",
                "grammar_config": {"tokenization": "cjk"},
            },
        )
    ).json()
    course = (
        await client.post(
            "/api/courses",
            json={
                "base_language_id": lang_en["id"],
                "target_language_id": lang_zh["id"],
                "name": "English to Chinese",
                "slug": f"en-zh-pastein-{suffix}",
            },
        )
    ).json()
    await _add_known_word(client, course["id"], "你好")

    resp = await client.post(
        "/api/paste-in/analyze", json={"course_id": course["id"], "text": "你好，市场。"}
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "".join(s["text"] for s in body["segments"]) == "你好，市场。"
    words = {s["text"]: s["is_known"] for s in body["segments"] if s["is_word"]}
    assert words["你好"] is True
    assert words["市场"] is False


async def test_translate_unknown_words_via_fake_llm(client: AsyncClient):
    course = await _make_course(client)
    fake = FakeLLMProvider(
        WordTranslationBatchResult(
            translations=[
                BatchWordTranslation(target_text="amiga", base_text="friend"),
                BatchWordTranslation(target_text="esdrújula", base_text="stress on the antepenult"),
            ]
        )
    )
    app.dependency_overrides[get_llm_provider] = lambda: fake

    resp = await client.post(
        "/api/paste-in/translate-unknown-words",
        json={"course_id": course["id"], "words": ["amiga", "esdrújula"]},
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["translations"] == [
        {"target_text": "amiga", "base_text": "friend"},
        {"target_text": "esdrújula", "base_text": "stress on the antepenult"},
    ]
    assert fake.call_count == 1


async def test_translate_unknown_words_dedupes_words_that_share_a_dictionary_form(
    client: AsyncClient,
):
    # "hablo" and "hablas" are different conjugations of the same verb --
    # translate_words resolves both to the infinitive "hablar", and the
    # route must not render that as two separate glossary rows.
    course = await _make_course(client)
    fake = FakeLLMProvider(
        WordTranslationBatchResult(
            translations=[
                BatchWordTranslation(target_text="hablar", base_text="to speak"),
                BatchWordTranslation(target_text="Hablar", base_text="to speak"),
            ]
        )
    )
    app.dependency_overrides[get_llm_provider] = lambda: fake

    resp = await client.post(
        "/api/paste-in/translate-unknown-words",
        json={"course_id": course["id"], "words": ["hablo", "hablas"]},
    )

    assert resp.status_code == 200, resp.text
    assert resp.json()["translations"] == [{"target_text": "hablar", "base_text": "to speak"}]


async def test_translate_unknown_words_with_empty_list_skips_the_llm_call(client: AsyncClient):
    course = await _make_course(client)
    fake = FakeLLMProvider(WordTranslationBatchResult(translations=[]))
    app.dependency_overrides[get_llm_provider] = lambda: fake

    resp = await client.post(
        "/api/paste-in/translate-unknown-words", json={"course_id": course["id"], "words": []}
    )

    assert resp.status_code == 200
    assert resp.json() == {"translations": []}
    assert fake.call_count == 0
