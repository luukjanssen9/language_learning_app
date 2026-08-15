"""Pure unit tests for the roleplay-chat service -- no DB, no HTTP client,
no real LLM call. Same convention as `test_sentence_generation.py`: a
minimal fake standing in for the real `LLMProvider` dependency.
"""

from pydantic import BaseModel

from app.services.journal_correction import Correction
from app.services.llm.base import ChatTurn, ModelTier
from app.services.roleplay_chat import (
    ChatReplyResult,
    continue_conversation,
    start_conversation,
)


class FakeLLMProvider:
    def __init__(self, canned_response: BaseModel) -> None:
        self.canned_response = canned_response
        self.last_prompt: str | None = None
        self.last_history: list[ChatTurn] | None = None
        self.last_model_tier: ModelTier | None = None
        self.call_count = 0

    async def generate_structured(
        self, prompt: str, response_model: type, model_tier: ModelTier = "fast"
    ) -> BaseModel:
        self.last_prompt = prompt
        self.last_model_tier = model_tier
        self.call_count += 1
        return self.canned_response

    async def generate_chat_reply(
        self,
        system_prompt: str,
        history: list[ChatTurn],
        response_model: type,
        model_tier: ModelTier = "fast",
    ) -> BaseModel:
        self.last_prompt = system_prompt
        self.last_history = history
        self.last_model_tier = model_tier
        self.call_count += 1
        return self.canned_response


async def test_start_conversation_returns_provider_result():
    canned = ChatReplyResult(reply_text="¡Hola! ¿Qué te gustaría tomar?", corrections=[])
    fake = FakeLLMProvider(canned)

    result = await start_conversation(
        fake,
        target_language_name="Spanish",
        base_language_name="English",
        scenario_setup_prompt="You are a barista.",
        known_words=["hola", "gracias"],
    )

    assert result == canned
    assert fake.last_model_tier == "reasoning"


async def test_start_conversation_prompt_uses_scenario_and_languages():
    fake = FakeLLMProvider(ChatReplyResult(reply_text="", corrections=[]))

    await start_conversation(
        fake,
        target_language_name="Dutch",
        base_language_name="English",
        scenario_setup_prompt="You are a hotel receptionist.",
        known_words=[],
    )

    assert fake.last_prompt is not None
    assert "Dutch" in fake.last_prompt
    assert "English" in fake.last_prompt
    assert "You are a hotel receptionist." in fake.last_prompt
    assert "Spanish" not in fake.last_prompt


async def test_start_conversation_uses_beginner_clause_when_no_known_words():
    fake = FakeLLMProvider(ChatReplyResult(reply_text="", corrections=[]))

    await start_conversation(
        fake,
        target_language_name="Spanish",
        base_language_name="English",
        scenario_setup_prompt="You are a barista.",
        known_words=[],
    )

    assert fake.last_prompt is not None
    assert "complete beginner" in fake.last_prompt


async def test_continue_conversation_calls_generate_chat_reply_with_full_history():
    canned = ChatReplyResult(
        reply_text="Claro, aquí tienes.",
        corrections=[
            Correction(
                original="quiero un cafe",
                corrected="quiero un café",
                explanation="missing accent",
            )
        ],
    )
    fake = FakeLLMProvider(canned)
    history = [
        ChatTurn(role="assistant", text="¡Hola! ¿Qué te gustaría tomar?"),
        ChatTurn(role="user", text="quiero un cafe"),
    ]

    result = await continue_conversation(
        fake,
        target_language_name="Spanish",
        base_language_name="English",
        scenario_setup_prompt="You are a barista.",
        known_words=["hola", "café"],
        history=history,
    )

    assert result == canned
    assert fake.last_history == history
    assert fake.last_model_tier == "reasoning"
    assert fake.last_prompt is not None
    assert "You are a barista." in fake.last_prompt
    assert "hola, café" in fake.last_prompt
