"""Integration tests for GET /vocabulary-items/{id}/audio, through the
live API + DB (`client`/`db_session` fixtures from conftest.py). The real
Google Cloud TTS client is swapped out via the same FastAPI
dependency-override mechanism already used for `get_db`/`get_llm_provider`.
"""

import uuid

from httpx import AsyncClient

from app.main import app
from app.services.tts import get_tts_client

TTS_CONFIG = {"tts": {"language_code": "es-ES", "voice_name": "es-ES-Standard-A"}}


class FakeTTSResponse:
    def __init__(self, audio_content: bytes) -> None:
        self.audio_content = audio_content


class FakeTTSClient:
    def __init__(self, audio_content: bytes = b"fake-mp3-bytes") -> None:
        self.audio_content = audio_content
        self.call_count = 0

    async def synthesize_speech(self, input, voice, audio_config):
        self.call_count += 1
        return FakeTTSResponse(self.audio_content)


async def _make_vocabulary_item(
    client: AsyncClient, *, target_grammar_config: dict | None = None
) -> dict:
    suffix = uuid.uuid4().hex[:6]  # Language.code is capped at String(10)
    lang_en = (
        await client.post("/api/languages", json={"code": f"en-{suffix}", "name": "English"})
    ).json()
    lang_es = (
        await client.post(
            "/api/languages",
            json={
                "code": f"es-{suffix}",
                "name": "Spanish",
                "grammar_config": target_grammar_config or {},
            },
        )
    ).json()
    course = (
        await client.post(
            "/api/courses",
            json={
                "base_language_id": lang_en["id"],
                "target_language_id": lang_es["id"],
                "name": "English to Spanish",
                "slug": f"en-es-audio-{suffix}",
            },
        )
    ).json()
    user = (
        await client.post(
            "/api/users",
            json={"email": f"audio-{suffix}@example.com", "display_name": "Audio Test"},
        )
    ).json()
    item = (
        await client.post(
            "/api/vocabulary-items",
            json={
                "course_id": course["id"],
                "user_id": user["id"],
                "target_text": "hola",
                "base_text": "hello",
            },
        )
    ).json()
    return item


async def test_generates_and_persists_audio_on_first_request(client: AsyncClient):
    item = await _make_vocabulary_item(client, target_grammar_config=TTS_CONFIG)
    fake = FakeTTSClient(audio_content=b"real-sounding-mp3-bytes")
    app.dependency_overrides[get_tts_client] = lambda: fake

    resp = await client.get(
        f"/api/vocabulary-items/{item['id']}/audio", params={"user_id": item["user_id"]}
    )

    assert resp.status_code == 200
    assert resp.content == b"real-sounding-mp3-bytes"
    assert resp.headers["content-type"] == "audio/mpeg"
    assert fake.call_count == 1


async def test_second_request_serves_cached_audio_without_calling_tts_again(
    client: AsyncClient,
):
    item = await _make_vocabulary_item(client, target_grammar_config=TTS_CONFIG)
    fake = FakeTTSClient()
    app.dependency_overrides[get_tts_client] = lambda: fake

    first = await client.get(
        f"/api/vocabulary-items/{item['id']}/audio", params={"user_id": item["user_id"]}
    )
    second = await client.get(
        f"/api/vocabulary-items/{item['id']}/audio", params={"user_id": item["user_id"]}
    )

    assert first.content == second.content
    assert fake.call_count == 1  # the second request was served from the DB, not regenerated


async def test_audio_for_language_without_tts_config_returns_404(client: AsyncClient):
    item = await _make_vocabulary_item(client, target_grammar_config={})
    app.dependency_overrides[get_tts_client] = lambda: FakeTTSClient()

    resp = await client.get(
        f"/api/vocabulary-items/{item['id']}/audio", params={"user_id": item["user_id"]}
    )

    assert resp.status_code == 404


async def test_audio_for_missing_vocabulary_item_returns_404(client: AsyncClient):
    app.dependency_overrides[get_tts_client] = lambda: FakeTTSClient()

    resp = await client.get(
        f"/api/vocabulary-items/{uuid.uuid4()}/audio", params={"user_id": uuid.uuid4()}
    )

    assert resp.status_code == 404


async def test_audio_for_someone_elses_vocabulary_item_is_403(client: AsyncClient):
    item = await _make_vocabulary_item(client, target_grammar_config=TTS_CONFIG)
    app.dependency_overrides[get_tts_client] = lambda: FakeTTSClient()

    resp = await client.get(
        f"/api/vocabulary-items/{item['id']}/audio", params={"user_id": uuid.uuid4()}
    )

    assert resp.status_code == 403
