"""Translates a single word via an `LLMProvider`, for the known-vocabulary
"promote" flow -- a `KnownVocabularyItem` only ever stores `target_text`
(no translation, per PLAN.md's 2026-08-14 "known-vocabulary system"
decision), so promoting one to a real `VocabularyItem` needs a translation
fetched at that moment. Pure function, no DB access -- same convention as
`sentence_generation.py`/`conjugation.py`; the prompt is built entirely
from arguments, never a hardcoded language name.
"""

from pydantic import BaseModel

from app.services.llm.base import LLMProvider


class WordTranslation(BaseModel):
    base_text: str
    part_of_speech: str | None = None


async def translate_word(
    llm: LLMProvider,
    target_language_name: str,
    base_language_name: str,
    word: str,
) -> WordTranslation:
    prompt = (
        f'Translate the {target_language_name} word "{word}" into {base_language_name}. '
        "Give the single most common translation (a short word or phrase, not a full "
        "sentence), and its part of speech if you're confident of one."
    )
    return await llm.generate_structured(prompt, WordTranslation, model_tier="fast")
