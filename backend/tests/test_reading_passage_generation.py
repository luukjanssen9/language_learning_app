"""Pure unit tests for the reading-passage generation service -- no DB, no
HTTP client, no real LLM call. Same convention as test_sentence_generation.py.
"""

from pydantic import BaseModel

from app.services.llm.base import ModelTier
from app.services.reading_passage_generation import (
    NewVocabularyWordResult,
    QuestionResult,
    ReadingPassageResult,
    generate_reading_passage,
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


def _canned() -> ReadingPassageResult:
    return ReadingPassageResult(
        target_text="Hola, ¿cómo estás?",
        base_text="Hello, how are you?",
        new_vocabulary=[NewVocabularyWordResult(target_text="estás", base_text="you are")],
        questions=[
            QuestionResult(question_text="¿Qué se pregunta?", reference_answer="Cómo estás")
        ],
    )


async def test_generate_reading_passage_returns_provider_result():
    fake = FakeLLMProvider(_canned())

    result = await generate_reading_passage(
        fake, "Spanish", "English", known_words=["hola", "como"]
    )

    assert result == _canned()


async def test_prompt_includes_known_words_and_no_hardcoded_language():
    # Dutch/English here specifically because this project's first-built
    # language was Spanish -- a test that only ever used Spanish wouldn't
    # catch a hardcoded "Spanish" slipping into the prompt.
    fake = FakeLLMProvider(_canned())

    await generate_reading_passage(fake, "Dutch", "English", known_words=["hallo", "dag"])

    assert fake.last_prompt is not None
    assert "Dutch" in fake.last_prompt
    assert "English" in fake.last_prompt
    assert "hallo" in fake.last_prompt
    assert "dag" in fake.last_prompt
    assert "Spanish" not in fake.last_prompt


async def test_empty_known_words_uses_beginner_fallback_instruction():
    fake = FakeLLMProvider(_canned())

    await generate_reading_passage(fake, "Spanish", "English", known_words=[])

    assert fake.last_prompt is not None
    assert "beginner" in fake.last_prompt


async def test_uses_reasoning_model_tier():
    fake = FakeLLMProvider(_canned())

    await generate_reading_passage(fake, "Spanish", "English", known_words=["hola"])

    assert fake.last_model_tier == "reasoning"


async def test_new_word_count_is_reflected_in_prompt():
    fake = FakeLLMProvider(_canned())

    await generate_reading_passage(
        fake, "Spanish", "English", known_words=["hola"], new_word_count=8
    )

    assert fake.last_prompt is not None
    assert "8" in fake.last_prompt
