"""Pure unit tests for the word-translation service -- no DB, no HTTP
client, no real LLM call. Same convention as test_sentence_generation.py.
"""

from pydantic import BaseModel

from app.services.llm.base import ModelTier
from app.services.word_translation import (
    BatchWordTranslation,
    WordTranslation,
    WordTranslationBatchResult,
    translate_word,
    translate_words,
)


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


async def test_translate_words_returns_the_providers_translation_list():
    canned = WordTranslationBatchResult(
        translations=[
            BatchWordTranslation(target_text="hola", base_text="hello"),
            BatchWordTranslation(target_text="gato", base_text="cat"),
        ]
    )
    fake = FakeLLMProvider(canned)

    result = await translate_words(fake, "Spanish", "English", ["hola", "gato"])

    assert result == canned.translations


async def test_translate_words_prompt_includes_every_word_and_no_hardcoded_language():
    fake = FakeLLMProvider(WordTranslationBatchResult(translations=[]))

    await translate_words(fake, "Dutch", "English", ["hallo", "dag"])

    assert fake.last_prompt is not None
    assert "Dutch" in fake.last_prompt
    assert "English" in fake.last_prompt
    assert "hallo" in fake.last_prompt
    assert "dag" in fake.last_prompt
    assert "Spanish" not in fake.last_prompt


async def test_translate_words_uses_fast_model_tier():
    fake = FakeLLMProvider(WordTranslationBatchResult(translations=[]))

    await translate_words(fake, "Spanish", "English", ["hola"])

    assert fake.last_model_tier == "fast"


# Regression test for a real bug found live (2026-08-14): the LLM
# returned target_text/base_text backwards (translation in target_text,
# original word in base_text) because the prompt named the two output
# fields without saying which language each one means -- Pydantic field
# names alone aren't enough context for the model to infer this
# correctly. The prompt must spell out target_text = original word,
# base_text = translation, explicitly.
async def test_translate_words_prompt_explains_target_text_and_base_text_explicitly():
    fake = FakeLLMProvider(WordTranslationBatchResult(translations=[]))

    await translate_words(fake, "Spanish", "English", ["hola"])

    assert fake.last_prompt is not None
    assert "target_text is the original Spanish word" in fake.last_prompt
    assert "base_text is its English translation" in fake.last_prompt
