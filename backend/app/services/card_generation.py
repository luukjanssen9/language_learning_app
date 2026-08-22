"""Generates a complete flashcard -- translation, part of speech, and one
example sentence -- from a single word in the course's base language, via
one LLM call. Backs the "type a word, get an AI-generated card" button on
a deck's page. Pure function, no DB access -- same convention as
word_translation.py/sentence_generation.py; the caller (route) persists
the result via note_cards.py.

Deliberately one combined LLM call rather than composing translate_word +
generate_example_sentences: those two calls together return far more than
this flow needs (3 examples + a mnemonic) and would double the latency a
user waits through after clicking the button for what is a single-word,
synchronous submission -- unlike paste-in's already-batched translate_words.
"""

from pydantic import BaseModel

from app.services.llm.base import LLMProvider


class GeneratedCard(BaseModel):
    target_text: str
    part_of_speech: str | None = None
    example_sentence: str
    example_sentence_translation: str


async def generate_card_from_word(
    llm: LLMProvider,
    target_language_name: str,
    base_language_name: str,
    base_word: str,
) -> GeneratedCard:
    prompt = (
        f'A language learner typed the {base_language_name} word "{base_word}" '
        f"and wants a {target_language_name} flashcard for it. Return:\n"
        f"- target_text: its single most common {target_language_name} translation, "
        "in dictionary/citation form (infinitive for a verb, singular for a noun, "
        "masculine singular for an adjective)\n"
        f"- part_of_speech: its part of speech in {target_language_name}, if you're "
        "confident of one\n"
        f"- example_sentence: one short, natural sentence in {target_language_name} "
        "using that word, appropriate for a beginner learner\n"
        f"- example_sentence_translation: that sentence's {base_language_name} "
        "translation"
    )
    return await llm.generate_structured(prompt, GeneratedCard, model_tier="fast")
