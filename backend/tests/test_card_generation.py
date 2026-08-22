"""Pure unit tests for the card-generation service -- no DB, no HTTP
client, no real LLM call. Same convention as test_word_translation.py.
"""

from pydantic import BaseModel

from app.services.card_generation import GeneratedCard, generate_card_from_word
from app.services.llm.base import ModelTier


class FakeLLMProvider:
    def __init__(self, canned_response: BaseModel) -> None:
        self.canned_response = canned_response
        self.last_prompt: str | None = None
        self.last_model_tier: ModelTier | None = None
        self.call_count = 0

    async def generate_structured(
        self, prompt: str, response_model: type, model_tier: ModelTier = "fast"
    ) -> BaseModel:
        self.last_prompt = prompt
        self.last_model_tier = model_tier
        self.call_count += 1
        return self.canned_response


async def test_generate_card_from_word_returns_provider_result():
    canned = GeneratedCard(
        target_text="hola",
        part_of_speech="interjection",
        example_sentence="Hola, ¿cómo estás?",
        example_sentence_translation="Hello, how are you?",
    )
    fake = FakeLLMProvider(canned)

    result = await generate_card_from_word(fake, "Spanish", "English", "hello")

    assert result == canned


async def test_generate_card_from_word_prompt_uses_passed_in_language_names():
    # Dutch/English specifically, same reasoning as
    # test_word_translation.py's equivalent test: this project's first
    # language pair was Spanish, so a test that only ever used Spanish
    # wouldn't catch a hardcoded "Spanish" slipping into the prompt.
    fake = FakeLLMProvider(
        GeneratedCard(
            target_text="hallo",
            example_sentence="Hallo!",
            example_sentence_translation="Hello!",
        )
    )

    await generate_card_from_word(fake, "Dutch", "English", "hello")

    assert fake.last_prompt is not None
    assert "Dutch" in fake.last_prompt
    assert "English" in fake.last_prompt
    assert "hello" in fake.last_prompt
    assert "Spanish" not in fake.last_prompt


async def test_generate_card_from_word_uses_fast_model_tier():
    fake = FakeLLMProvider(
        GeneratedCard(
            target_text="hola",
            example_sentence="Hola.",
            example_sentence_translation="Hello.",
        )
    )

    await generate_card_from_word(fake, "Spanish", "English", "hello")

    assert fake.last_model_tier == "fast"


async def test_generate_card_from_word_only_calls_the_llm_once():
    # The whole point of a combined prompt over translate_word +
    # generate_example_sentences -- a single word/click should mean a
    # single round trip, not two.
    fake = FakeLLMProvider(
        GeneratedCard(
            target_text="hola",
            example_sentence="Hola.",
            example_sentence_translation="Hello.",
        )
    )

    await generate_card_from_word(fake, "Spanish", "English", "hello")

    assert fake.call_count == 1
