"""Pure unit tests for the reading-comprehension grading service -- no DB,
no HTTP client, no real LLM call. Same convention as test_free_text_grading.py.
"""

from pydantic import BaseModel

from app.services.llm.base import ModelTier
from app.services.reading_comprehension_grading import (
    ComprehensionGradeResult,
    grade_comprehension_answer,
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


async def test_grade_comprehension_answer_returns_provider_result():
    canned = ComprehensionGradeResult(is_correct=True, feedback="Nicely done.")
    fake = FakeLLMProvider(canned)

    result = await grade_comprehension_answer(
        fake,
        passage_text="Ana va al mercado.",
        question_text="¿A dónde va Ana?",
        reference_answer="Al mercado",
        submitted_answer="Va al mercado",
    )

    assert result == canned


async def test_prompt_includes_passage_question_and_both_answers():
    fake = FakeLLMProvider(ComprehensionGradeResult(is_correct=False, feedback="Not quite."))

    await grade_comprehension_answer(
        fake,
        passage_text="Ana va al mercado.",
        question_text="¿A dónde va Ana?",
        reference_answer="Al mercado",
        submitted_answer="A la escuela",
    )

    assert fake.last_prompt is not None
    assert "Ana va al mercado." in fake.last_prompt
    assert "¿A dónde va Ana?" in fake.last_prompt
    assert "Al mercado" in fake.last_prompt
    assert "A la escuela" in fake.last_prompt


async def test_uses_reasoning_model_tier():
    fake = FakeLLMProvider(ComprehensionGradeResult(is_correct=True, feedback="Good."))

    await grade_comprehension_answer(
        fake,
        passage_text="Passage.",
        question_text="Question?",
        reference_answer="Answer.",
        submitted_answer="Answer.",
    )

    assert fake.last_model_tier == "reasoning"
