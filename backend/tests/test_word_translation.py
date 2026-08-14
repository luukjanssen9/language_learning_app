"""Pure unit tests for the word-translation service -- no DB, no HTTP
client, no real LLM call. Same convention as test_sentence_generation.py.
"""

from pydantic import BaseModel

from app.services.llm.base import ModelTier
from app.services.word_translation import WordTranslation, translate_word


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


async def test_translate_word_returns_provider_translation():
    canned = WordTranslation(base_text="hello", part_of_speech="interjection")
    fake = FakeLLMProvider(canned)

    result = await translate_word(fake, "Spanish", "English", "hola")

    assert result == canned


async def test_translate_word_prompt_uses_passed_in_language_names():
    # Dutch/English here specifically because this project's first-built
    # language was Spanish -- a test that only ever used Spanish wouldn't
    # catch a hardcoded "Spanish" slipping into the prompt.
    fake = FakeLLMProvider(WordTranslation(base_text="hello"))

    await translate_word(fake, "Dutch", "English", "hallo")

    assert fake.last_prompt is not None
    assert "Dutch" in fake.last_prompt
    assert "English" in fake.last_prompt
    assert "hallo" in fake.last_prompt
    assert "Spanish" not in fake.last_prompt


async def test_translate_word_uses_fast_model_tier():
    fake = FakeLLMProvider(WordTranslation(base_text="hello"))

    await translate_word(fake, "Spanish", "English", "hola")

    assert fake.last_model_tier == "fast"
