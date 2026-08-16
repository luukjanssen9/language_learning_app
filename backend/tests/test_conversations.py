"""Integration tests for the roleplay conversation endpoints, through the
live API + DB (`client`/`db_session` fixtures from conftest.py). The real
Gemini provider is swapped out via the same FastAPI dependency-override
mechanism used for `get_db` -- `app.dependency_overrides` is cleared by the
`client` fixture's own teardown.
"""

import uuid

from httpx import AsyncClient
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.roleplay import RoleplayScenario
from app.services.journal_correction import Correction
from app.services.llm import get_llm_provider
from app.services.llm.base import ChatTurn, ModelTier
from app.services.roleplay_chat import ChatReplyResult


class FakeLLMProvider:
    def __init__(self, canned_response: BaseModel) -> None:
        self.canned_response = canned_response
        self.call_count = 0
        self.last_history: list[ChatTurn] | None = None

    async def generate_structured(
        self, prompt: str, response_model: type, model_tier: ModelTier = "fast"
    ) -> BaseModel:
        self.call_count += 1
        return self.canned_response

    async def generate_chat_reply(
        self,
        system_prompt: str,
        history: list[ChatTurn],
        response_model: type,
        model_tier: ModelTier = "fast",
    ) -> BaseModel:
        self.call_count += 1
        self.last_history = history
        return self.canned_response


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
                "slug": f"en-es-roleplay-{suffix}",
            },
        )
    ).json()
    user = (
        await client.post(
            "/api/users",
            json={"email": f"roleplay-{suffix}@example.com", "display_name": "Roleplay Test"},
        )
    ).json()
    await login_as(user["id"])
    return {"course_id": course["id"], "user_id": user["id"]}


async def _make_scenario(db_session: AsyncSession, *, slug: str = "test-scenario") -> str:
    scenario = RoleplayScenario(
        name="Test scenario", slug=slug, setup_prompt="You are a friendly shopkeeper."
    )
    db_session.add(scenario)
    await db_session.flush()
    return str(scenario.id)


async def test_list_roleplay_scenarios_returns_seeded_scenarios(
    client: AsyncClient, db_session: AsyncSession
):
    await _make_scenario(db_session, slug="list-test-scenario")

    resp = await client.get("/api/roleplay-scenarios")

    assert resp.status_code == 200
    scenarios = resp.json()
    assert any(s["slug"] == "list-test-scenario" for s in scenarios)


async def test_create_conversation_generates_opening_message(
    client: AsyncClient, db_session: AsyncSession, login_as
):
    ctx = await _make_course(client, login_as)
    scenario_id = await _make_scenario(db_session)
    fake = FakeLLMProvider(ChatReplyResult(reply_text="¡Bienvenido a mi tienda!", corrections=[]))
    app.dependency_overrides[get_llm_provider] = lambda: fake

    resp = await client.post(
        "/api/conversations",
        json={"course_id": ctx["course_id"], "scenario_id": scenario_id},
    )

    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["conversation"]["scenario_id"] == scenario_id
    assert len(body["messages"]) == 1
    assert body["messages"][0]["role"] == "assistant"
    assert body["messages"][0]["text"] == "¡Bienvenido a mi tienda!"
    # Null, not an empty list, for assistant rows -- "no corrections"
    # doesn't apply to them at all (see ConversationMessage.corrections).
    assert body["messages"][0]["corrections"] is None
    assert fake.call_count == 1


async def test_send_message_persists_corrections_and_replies_in_character(
    client: AsyncClient, db_session: AsyncSession, login_as
):
    ctx = await _make_course(client, login_as)
    scenario_id = await _make_scenario(db_session, slug="send-message-scenario")
    start_fake = FakeLLMProvider(ChatReplyResult(reply_text="¿Qué necesitas?", corrections=[]))
    app.dependency_overrides[get_llm_provider] = lambda: start_fake
    conversation = (
        await client.post(
            "/api/conversations",
            json={"course_id": ctx["course_id"], "scenario_id": scenario_id},
        )
    ).json()["conversation"]

    reply_fake = FakeLLMProvider(
        ChatReplyResult(
            reply_text="Aquí tienes, son cinco euros.",
            corrections=[
                Correction(
                    original="quiero un pan",
                    corrected="quiero pan",
                    explanation="no article needed here",
                )
            ],
        )
    )
    app.dependency_overrides[get_llm_provider] = lambda: reply_fake

    resp = await client.post(
        f"/api/conversations/{conversation['id']}/messages",
        json={"text": "quiero un pan"},
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["user_message"]["text"] == "quiero un pan"
    assert body["user_message"]["corrections"] == [
        {
            "original": "quiero un pan",
            "corrected": "quiero pan",
            "explanation": "no article needed here",
        }
    ]
    assert body["assistant_message"]["role"] == "assistant"
    assert body["assistant_message"]["text"] == "Aquí tienes, son cinco euros."
    # The opening message plus this user turn -- confirms continue_conversation
    # was given the real prior history, not just the new message alone.
    assert reply_fake.last_history is not None
    assert len(reply_fake.last_history) == 2
    assert reply_fake.last_history[0].role == "assistant"
    assert reply_fake.last_history[1].role == "user"


async def test_list_conversation_messages_returns_full_transcript_in_order(
    client: AsyncClient, db_session: AsyncSession, login_as
):
    ctx = await _make_course(client, login_as)
    scenario_id = await _make_scenario(db_session, slug="transcript-scenario")
    app.dependency_overrides[get_llm_provider] = lambda: FakeLLMProvider(
        ChatReplyResult(reply_text="Hola.", corrections=[])
    )
    conversation = (
        await client.post(
            "/api/conversations",
            json={"course_id": ctx["course_id"], "scenario_id": scenario_id},
        )
    ).json()["conversation"]
    await client.post(
        f"/api/conversations/{conversation['id']}/messages",
        json={"text": "Hola tambien"},
    )

    resp = await client.get(f"/api/conversations/{conversation['id']}/messages")

    assert resp.status_code == 200
    messages = resp.json()
    assert [m["role"] for m in messages] == ["assistant", "user", "assistant"]


async def test_list_conversations_scoped_to_user_and_course(
    client: AsyncClient, db_session: AsyncSession, login_as
):
    ctx_a = await _make_course(client, login_as)
    scenario_id = await _make_scenario(db_session, slug="scoping-scenario")
    app.dependency_overrides[get_llm_provider] = lambda: FakeLLMProvider(
        ChatReplyResult(reply_text="Hola.", corrections=[])
    )
    await client.post(
        "/api/conversations",
        json={"course_id": ctx_a["course_id"], "scenario_id": scenario_id},
    )

    ctx_b = await _make_course(client, login_as)
    await client.post(
        "/api/conversations",
        json={"course_id": ctx_b["course_id"], "scenario_id": scenario_id},
    )

    await login_as(ctx_a["user_id"])
    resp = await client.get(
        "/api/conversations", params={"course_id": ctx_a["course_id"]}
    )

    assert resp.status_code == 200
    conversations = resp.json()
    assert len(conversations) == 1
    assert conversations[0]["user_id"] == ctx_a["user_id"]


async def test_list_someone_elses_conversation_messages_is_403(
    client: AsyncClient, db_session: AsyncSession, login_as
):
    ctx = await _make_course(client, login_as)
    other_user_resp = await client.post(
        "/api/users", json={"email": "not-in-convo@example.com", "display_name": "Not In Convo"}
    )
    other_user_id = other_user_resp.json()["id"]
    scenario_id = await _make_scenario(db_session, slug="messages-403-scenario")
    app.dependency_overrides[get_llm_provider] = lambda: FakeLLMProvider(
        ChatReplyResult(reply_text="Hola.", corrections=[])
    )
    conversation = (
        await client.post(
            "/api/conversations",
            json={"course_id": ctx["course_id"], "scenario_id": scenario_id},
        )
    ).json()["conversation"]

    await login_as(other_user_id)
    resp = await client.get(f"/api/conversations/{conversation['id']}/messages")
    assert resp.status_code == 403


async def test_send_message_to_someone_elses_conversation_is_403(
    client: AsyncClient, db_session: AsyncSession, login_as
):
    ctx = await _make_course(client, login_as)
    other_user_resp = await client.post(
        "/api/users", json={"email": "not-a-participant@example.com", "display_name": "Nope"}
    )
    other_user_id = other_user_resp.json()["id"]
    scenario_id = await _make_scenario(db_session, slug="send-403-scenario")
    app.dependency_overrides[get_llm_provider] = lambda: FakeLLMProvider(
        ChatReplyResult(reply_text="Hola.", corrections=[])
    )
    conversation = (
        await client.post(
            "/api/conversations",
            json={"course_id": ctx["course_id"], "scenario_id": scenario_id},
        )
    ).json()["conversation"]

    await login_as(other_user_id)
    resp = await client.post(
        f"/api/conversations/{conversation['id']}/messages", json={"text": "hola"}
    )
    assert resp.status_code == 403
