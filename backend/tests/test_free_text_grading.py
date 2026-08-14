"""Pure unit tests for the free-text-grading service -- no DB, no HTTP
client, no real LLM call. Same convention as `test_sentence_generation.py`:
a minimal fake standing in for `LLMProvider`.
"""

from pydantic import BaseModel

from app.services.free_text_grading import FreeTextGradeResult, grade_free_text_attempt
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


async def test_grade_free_text_attempt_returns_provider_result():
    canned = FreeTextGradeResult(is_correct=True, feedback="Nicely done.")
    fake = FakeLLMProvider(canned)

    result = await grade_free_text_attempt(
        fake,
        target_language_name="Spanish",
        base_language_name="English",
        prompt={"source_text": "Thank you very much for your help."},
        submitted_text="Muchas gracias por tu ayuda.",
    )

    assert result == canned


async def test_translation_style_prompt_includes_source_text():
    fake = FakeLLMProvider(FreeTextGradeResult(is_correct=True, feedback=""))

    await grade_free_text_attempt(
        fake,
        target_language_name="Spanish",
        base_language_name="English",
        prompt={"source_text": "Thank you very much for your help."},
        submitted_text="Muchas gracias por tu ayuda.",
    )

    assert fake.last_prompt is not None
    assert "Thank you very much for your help." in fake.last_prompt
    assert "Muchas gracias por tu ayuda." in fake.last_prompt


async def test_open_ended_style_prompt_includes_question_text():
    fake = FakeLLMProvider(FreeTextGradeResult(is_correct=True, feedback=""))

    await grade_free_text_attempt(
        fake,
        target_language_name="Spanish",
        base_language_name="English",
        prompt={"question_text": "¿Cómo te llamas?"},
        submitted_text="Me llamo Luuk.",
    )

    assert fake.last_prompt is not None
    assert "¿Cómo te llamas?" in fake.last_prompt
    assert "Me llamo Luuk." in fake.last_prompt
    # No source_text in this prompt shape, so the translation-style
    # instruction clause must not appear.
    assert "translate" not in fake.last_prompt.lower()


async def test_prompt_uses_passed_in_language_names_not_hardcoded():
    # Dutch/English specifically because this project's default/first-built
    # language was Spanish -- a test that only ever used Spanish wouldn't
    # catch a hardcoded "Spanish" slipping in.
    fake = FakeLLMProvider(FreeTextGradeResult(is_correct=True, feedback=""))

    await grade_free_text_attempt(
        fake,
        target_language_name="Dutch",
        base_language_name="English",
        prompt={"source_text": "Good morning."},
        submitted_text="Goedemorgen.",
    )

    assert fake.last_prompt is not None
    assert "Dutch" in fake.last_prompt
    assert "English" in fake.last_prompt
    assert "Spanish" not in fake.last_prompt


async def test_grade_free_text_attempt_uses_reasoning_model_tier():
    fake = FakeLLMProvider(FreeTextGradeResult(is_correct=True, feedback=""))

    await grade_free_text_attempt(
        fake,
        target_language_name="Spanish",
        base_language_name="English",
        prompt={"source_text": "Good morning."},
        submitted_text="Buenos días.",
    )

    assert fake.last_model_tier == "reasoning"
