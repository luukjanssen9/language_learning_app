"""Integration tests for POST /cards/generate, through the live API + DB
(same `client`/`db_session` fixtures as test_quick_add_and_gating.py). The
real LLM provider is swapped out via the same dependency-override
mechanism used in test_journal_entries.py/test_rate_limit.py.
"""

import uuid

from httpx import AsyncClient

from app.main import app
from app.services.card_generation import GeneratedCard
from app.services.llm import get_llm_provider


class FakeLLMProvider:
    def __init__(self, result: GeneratedCard) -> None:
        self.result = result
        self.call_count = 0

    async def generate_structured(self, prompt, response_model, model_tier="fast"):
        self.call_count += 1
        return self.result


async def _make_deck(client: AsyncClient, login_as) -> dict:
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
                "slug": f"en-es-cardgen-{suffix}",
            },
        )
    ).json()
    user = (
        await client.post(
            "/api/users",
            json={"email": f"cardgen-{suffix}@example.com", "display_name": "Card Gen Test"},
        )
    ).json()
    await login_as(user["id"])
    deck = (
        await client.post("/api/decks", json={"course_id": course["id"], "name": "Spanish deck"})
    ).json()
    return deck


def _canned_card() -> GeneratedCard:
    return GeneratedCard(
        target_text="hola",
        part_of_speech="interjection",
        example_sentence="Hola, ¿cómo estás?",
        example_sentence_translation="Hello, how are you?",
    )


CHINESE_LIKE_CONFIG = {
    "vocab_deck": {
        "dual_direction_cards": True,
        "needs_transliteration": True,
        "transliteration_label": "Pinyin",
    }
}


async def _make_chinese_deck(client: AsyncClient, login_as) -> dict:
    suffix = uuid.uuid4().hex[:6]
    lang_en = (
        await client.post("/api/languages", json={"code": f"en-{suffix}", "name": "English"})
    ).json()
    lang_zh = (
        await client.post(
            "/api/languages",
            json={"code": f"zh-{suffix}", "name": "Chinese", "grammar_config": CHINESE_LIKE_CONFIG},
        )
    ).json()
    course = (
        await client.post(
            "/api/courses",
            json={
                "base_language_id": lang_en["id"],
                "target_language_id": lang_zh["id"],
                "name": "English to Chinese",
                "slug": f"en-zh-cardgen-{suffix}",
            },
        )
    ).json()
    user = (
        await client.post(
            "/api/users",
            json={"email": f"cardgen-zh-{suffix}@example.com", "display_name": "Card Gen ZH Test"},
        )
    ).json()
    await login_as(user["id"])
    deck = (
        await client.post("/api/decks", json={"course_id": course["id"], "name": "Chinese deck"})
    ).json()
    return deck


async def test_generate_card_creates_a_note_and_card_from_an_english_word(
    client: AsyncClient, login_as
):
    deck = await _make_deck(client, login_as)
    app.dependency_overrides[get_llm_provider] = lambda: FakeLLMProvider(_canned_card())

    resp = await client.post(
        "/api/cards/generate", json={"deck_id": deck["id"], "base_text": "hello"}
    )

    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["vocabulary_item"]["target_text"] == "hola"
    assert body["vocabulary_item"]["base_text"] == "hello"
    assert body["vocabulary_item"]["part_of_speech"] == "interjection"
    assert body["vocabulary_item"]["example_sentence"] == "Hola, ¿cómo estás?"
    assert body["vocabulary_item"]["source"] == "AI-generated"
    assert len(body["cards"]) == 1
    assert body["cards"][0]["state"] == "new"


async def test_generate_card_reuses_an_existing_note_idempotently(client: AsyncClient, login_as):
    deck = await _make_deck(client, login_as)
    app.dependency_overrides[get_llm_provider] = lambda: FakeLLMProvider(_canned_card())

    first = await client.post(
        "/api/cards/generate", json={"deck_id": deck["id"], "base_text": "hello"}
    )
    second = await client.post(
        "/api/cards/generate", json={"deck_id": deck["id"], "base_text": "hello"}
    )

    assert first.json()["vocabulary_item"]["id"] == second.json()["vocabulary_item"]["id"]
    assert first.json()["cards"][0]["id"] == second.json()["cards"][0]["id"]


async def test_generate_card_into_another_users_deck_is_403(client: AsyncClient, login_as):
    deck = await _make_deck(client, login_as)
    other_user_resp = await client.post(
        "/api/users", json={"email": "not-the-owner@example.com", "display_name": "Not Owner"}
    )
    other_user_id = other_user_resp.json()["id"]
    await login_as(other_user_id)
    app.dependency_overrides[get_llm_provider] = lambda: FakeLLMProvider(_canned_card())

    resp = await client.post(
        "/api/cards/generate", json={"deck_id": deck["id"], "base_text": "hello"}
    )

    assert resp.status_code == 403


async def test_generate_card_stores_transliteration_for_a_language_that_needs_one(
    client: AsyncClient, login_as
):
    deck = await _make_chinese_deck(client, login_as)
    app.dependency_overrides[get_llm_provider] = lambda: FakeLLMProvider(
        GeneratedCard(
            target_text="早饭",
            part_of_speech="noun",
            transliteration="zǎofàn",
            example_sentence="我吃早饭。",
            example_sentence_translation="I eat breakfast.",
            example_sentence_transliteration="Wǒ chī zǎofàn.",
        )
    )

    resp = await client.post(
        "/api/cards/generate", json={"deck_id": deck["id"], "base_text": "breakfast"}
    )

    assert resp.status_code == 201, resp.text
    attributes = resp.json()["vocabulary_item"]["attributes"]
    assert attributes["transliteration"] == "zǎofàn"
    assert attributes["example_sentence_transliteration"] == "Wǒ chī zǎofàn."


async def test_generate_card_omits_transliteration_when_the_language_does_not_need_one(
    client: AsyncClient, login_as
):
    deck = await _make_deck(client, login_as)
    app.dependency_overrides[get_llm_provider] = lambda: FakeLLMProvider(_canned_card())

    resp = await client.post(
        "/api/cards/generate", json={"deck_id": deck["id"], "base_text": "hello"}
    )

    assert resp.status_code == 201, resp.text
    assert resp.json()["vocabulary_item"]["attributes"] == {}


async def test_generate_card_endpoint_429s_once_its_budget_is_exhausted(
    client: AsyncClient, login_as
):
    from app.api.rate_limit import card_generation_limiter

    deck = await _make_deck(client, login_as)
    app.dependency_overrides[get_llm_provider] = lambda: FakeLLMProvider(_canned_card())

    for i in range(card_generation_limiter.max_calls):
        resp = await client.post(
            "/api/cards/generate", json={"deck_id": deck["id"], "base_text": f"word{i}"}
        )
        assert resp.status_code == 201, resp.text

    resp = await client.post(
        "/api/cards/generate", json={"deck_id": deck["id"], "base_text": "one_too_many"}
    )
    assert resp.status_code == 429
