"""Corrects a user's free-form target-language writing via an
`LLMProvider`. Pure function, no DB access -- same convention as
`sentence_generation.py`/`free_text_grading.py`; the caller (route) is
responsible for persisting the result as a `JournalEntry`.
"""

from pydantic import BaseModel

from app.services.llm.base import LLMProvider


class Correction(BaseModel):
    original: str
    corrected: str
    explanation: str


class VocabSuggestion(BaseModel):
    target_text: str
    base_text: str
    example_sentence: str


class JournalCorrectionResult(BaseModel):
    corrected_text: str
    overall_feedback: str
    corrections: list[Correction]
    vocabulary_suggestions: list[VocabSuggestion]


async def correct_journal_entry(
    llm: LLMProvider,
    target_language_name: str,
    base_language_name: str,
    submitted_text: str,
) -> JournalCorrectionResult:
    prompt = (
        f"A {base_language_name}-speaking learner of {target_language_name} "
        f'wrote this journal entry in {target_language_name}:\n"{submitted_text}"\n\n'
        "Correct it. Return:\n"
        "- corrected_text: the full entry rewritten correctly.\n"
        "- overall_feedback: one brief, encouraging sentence about the entry as a "
        "whole.\n"
        "- corrections: a list of the specific real grammar/vocabulary errors "
        "found (not stylistic nitpicks or equally-valid alternate phrasings), "
        "each as {original, corrected, explanation} -- the smallest original "
        "snippet that was wrong, what it should be, and why, in one short "
        "sentence.\n"
        "- vocabulary_suggestions: words or short phrases the learner used "
        "CORRECTLY that are likely new or intermediate-level for them and worth "
        "adding to a flashcard deck, each as {target_text, base_text, "
        "example_sentence} -- example_sentence is the corrected sentence it "
        "appeared in. Never include a word that was actually misused (that "
        "belongs in corrections instead, not here)."
    )
    return await llm.generate_structured(
        prompt, JournalCorrectionResult, model_tier="reasoning"
    )
