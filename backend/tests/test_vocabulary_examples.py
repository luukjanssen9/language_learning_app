"""Integration tests for GET /vocabulary-items/{id}/examples, through the
live API + DB (`client`/`db_session` fixtures from conftest.py). The real
Gemini provider is swapped out via the same FastAPI dependency-override
mechanism already used for `get_db` (conftest.py) -- `app.dependency_overrides`
is cleared by the `client` fixture's own teardown, so no extra cleanup is
needed here.
"""

import uuid

from httpx import AsyncClient
from pydantic import BaseModel

from app.main import app
from app.services.llm import get_llm_provider
from app.services.llm.base import ModelTier
from app.services.sentence_generation import ExampleSentence, ExampleSentenceList


class FakeLLMProvider:
    def __init__(self, canned_response: BaseModel) -> None:
        self.canned_response = canned_response
        self.call_count = 0

    async def generate_structured(
        self, prompt: str, response_model: type, model_tier: ModelTier = "fast"
    ) -> BaseModel:
        self.call_count += 1
        return self.canned_response


async def _make_vocabulary_item(
    client: AsyncClient, *, target_name: str = "Spanish", target_code_prefix: str = "es"
) -> dict:
    suffix = uuid.uuid4().hex[:6]  # Language.code is capped at String(10)
    lang_en = (
        await client.post("/api/languages", json={"code": f"en-{suffix}", "name": "English"})
    ).json()
    lang_target = (
        await client.post(
            "/api/languages", json={"code": f"{target_code_prefix}-{suffix}", "name": target_name}
        )
    ).json()
    course = (
        await client.post(
            "/api/courses",
            json={
                "base_language_id": lang_en["id"],
                "target_language_id": lang_target["id"],
                "name": f"English to {target_name}",
                "slug": f"en-{target_code_prefix}-examples-{suffix}",
            },
        )
    ).json()
    user = (
        await client.post(
            "/api/users",
            json={"email": f"vocabexamples-{suffix}@example.com", "display_name": "Examples Test"},
        )
    ).json()
    item = (
        await client.post(
            "/api/vocabulary-items",
            json={
                "course_id": course["id"],
                "user_id": user["id"],
                "target_text": "hola" if target_name == "Spanish" else "hallo",
                "base_text": "hello",
                "part_of_speech": "interjection",
            },
        )
    ).json()
    return item


async def test_generates_and_persists_examples_on_first_request(client: AsyncClient):
    item = await _make_vocabulary_item(client)
    fake = FakeLLMProvider(
        ExampleSentenceList(
            examples=[
                ExampleSentence(target_text="¡Hola!", base_text="Hello!"),
                ExampleSentence(target_text="Hola, ¿qué tal?", base_text="Hi, how's it going?"),
                ExampleSentence(target_text="Hola de nuevo.", base_text="Hello again."),
            ],
            mnemonic="Sounds like 'Oh, la!' -- a cheerful greeting.",
        )
    )
    app.dependency_overrides[get_llm_provider] = lambda: fake

    resp = await client.get(
        f"/api/vocabulary-items/{item['id']}/examples", params={"user_id": item["user_id"]}
    )

    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 3
    assert {e["target_text"] for e in body} == {"¡Hola!", "Hola, ¿qué tal?", "Hola de nuevo."}
    # The one shared mnemonic is duplicated onto every persisted row.
    assert {e["mnemonic"] for e in body} == {"Sounds like 'Oh, la!' -- a cheerful greeting."}
    assert fake.call_count == 1


async def test_second_request_serves_cached_examples_without_calling_llm_again(
    client: AsyncClient,
):
    item = await _make_vocabulary_item(client)
    fake = FakeLLMProvider(
        ExampleSentenceList(
            examples=[ExampleSentence(target_text="¡Hola!", base_text="Hello!")],
            mnemonic="Sounds like 'Oh, la!'",
        )
    )
    app.dependency_overrides[get_llm_provider] = lambda: fake

    first = await client.get(
        f"/api/vocabulary-items/{item['id']}/examples", params={"user_id": item["user_id"]}
    )
    second = await client.get(
        f"/api/vocabulary-items/{item['id']}/examples", params={"user_id": item["user_id"]}
    )

    assert first.json() == second.json()
    assert fake.call_count == 1  # the second request was served from the DB, not regenerated


async def test_examples_for_missing_vocabulary_item_returns_404(client: AsyncClient):
    app.dependency_overrides[get_llm_provider] = lambda: FakeLLMProvider(
        ExampleSentenceList(examples=[], mnemonic="")
    )

    resp = await client.get(
        f"/api/vocabulary-items/{uuid.uuid4()}/examples", params={"user_id": uuid.uuid4()}
    )

    assert resp.status_code == 404


async def test_examples_for_someone_elses_vocabulary_item_is_403(client: AsyncClient):
    item = await _make_vocabulary_item(client)
    app.dependency_overrides[get_llm_provider] = lambda: FakeLLMProvider(
        ExampleSentenceList(examples=[], mnemonic="")
    )

    resp = await client.get(
        f"/api/vocabulary-items/{item['id']}/examples", params={"user_id": uuid.uuid4()}
    )

    assert resp.status_code == 403
