"""Translates one or many words via an `LLMProvider`.

`translate_word` backs the known-vocabulary "promote" flow -- a
`KnownVocabularyItem` only ever stores `target_text` (no translation, per
PLAN.md's 2026-08-14 "known-vocabulary system" decision), so promoting one
to a real `VocabularyItem` needs a translation fetched at that moment.

`translate_words` backs paste-in unknown-word flagging -- translating each
flagged word one at a time would mean one LLM call per word for a pasted
article that could have dozens; this batches them into a single call
instead.

Both are pure functions, no DB access -- same convention as
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


class BatchWordTranslation(BaseModel):
    # Unlike WordTranslation above, this carries its own target_text --
    # a structured LLM response over a list isn't guaranteed to preserve
    # positional order, so each output item must self-identify which
    # input word it translates rather than being matched up by index.
    target_text: str
    base_text: str


class WordTranslationBatchResult(BaseModel):
    translations: list[BatchWordTranslation]


async def translate_words(
    llm: LLMProvider,
    target_language_name: str,
    base_language_name: str,
    words: list[str],
) -> list[BatchWordTranslation]:
    word_list = ", ".join(f'"{w}"' for w in words)
    prompt = (
        f"Translate each of these {target_language_name} words into "
        f"{base_language_name}, giving the single most common translation "
        f"(a short word or phrase, not a full sentence) for each: {word_list}. "
        "Return exactly one entry per word listed, each as {target_text, base_text} "
        f"-- target_text is the original {target_language_name} word exactly as "
        f"given (do not translate it into this field), base_text is its "
        f"{base_language_name} translation."
    )
    result = await llm.generate_structured(
        prompt, WordTranslationBatchResult, model_tier="fast"
    )
    return result.translations
