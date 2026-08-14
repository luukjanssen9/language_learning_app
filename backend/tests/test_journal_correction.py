"""Pure unit tests for the journal-correction service -- no DB, no HTTP
client, no real LLM call. Same convention as `test_free_text_grading.py`/
`test_sentence_generation.py`: a minimal fake standing in for
`LLMProvider`.
"""

from pydantic import BaseModel

from app.services.journal_correction import (
    Correction,
    JournalCorrectionResult,
    VocabSuggestion,
    correct_journal_entry,
)
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


def _canned() -> JournalCorrectionResult:
    return JournalCorrectionResult(
        corrected_text="Ayer fui al mercado y compré manzanas.",
        overall_feedback="Nice work, just one small tense slip.",
        corrections=[
            Correction(
                original="ayer voy",
                corrected="ayer fui",
                explanation="Past events use the preterite, not the present.",
            )
        ],
        vocabulary_suggestions=[
            VocabSuggestion(
                target_text="el mercado",
                base_text="the market",
                example_sentence="Ayer fui al mercado y compré manzanas.",
            )
        ],
    )


async def test_correct_journal_entry_returns_provider_result():
    canned = _canned()
    fake = FakeLLMProvider(canned)

    result = await correct_journal_entry(
        fake,
        target_language_name="Spanish",
        base_language_name="English",
        submitted_text="Ayer voy al mercado y compré manzanas.",
    )

    assert result == canned


async def test_prompt_includes_the_submitted_text():
    fake = FakeLLMProvider(_canned())

    await correct_journal_entry(
        fake,
        target_language_name="Spanish",
        base_language_name="English",
        submitted_text="Ayer voy al mercado y compré manzanas.",
    )

    assert fake.last_prompt is not None
    assert "Ayer voy al mercado y compré manzanas." in fake.last_prompt


async def test_prompt_uses_passed_in_language_names_not_hardcoded():
    # Dutch/English specifically because this project's default/first-built
    # language was Spanish -- a test that only ever used Spanish wouldn't
    # catch a hardcoded "Spanish" slipping in.
    fake = FakeLLMProvider(_canned())

    await correct_journal_entry(
        fake,
        target_language_name="Dutch",
        base_language_name="English",
        submitted_text="Ik gaan naar de markt.",
    )

    assert fake.last_prompt is not None
    assert "Dutch" in fake.last_prompt
    assert "English" in fake.last_prompt
    assert "Spanish" not in fake.last_prompt


async def test_correct_journal_entry_uses_reasoning_model_tier():
    fake = FakeLLMProvider(_canned())

    await correct_journal_entry(
        fake,
        target_language_name="Spanish",
        base_language_name="English",
        submitted_text="Ayer voy al mercado.",
    )

    assert fake.last_model_tier == "reasoning"
