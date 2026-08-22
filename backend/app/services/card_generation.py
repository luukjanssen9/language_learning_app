"""Generates a complete flashcard -- translation, part of speech, an
example sentence, and (for a script the target language's `vocab_deck`
config flags as needing one) a transliteration -- from a single word in
the course's base language, via one LLM call. Backs the "type a word, get
an AI-generated card" button on a deck's page. Pure functions, no DB
access -- same convention as word_translation.py/sentence_generation.py;
the caller (route) persists the result via note_cards.py, storing the
transliteration fields in VocabularyItem.attributes the same way the
manual quick-add form does (see QuickAddButton.tsx).

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
    # Only populated when the caller passes a transliteration_label (i.e.
    # the target language's vocab_deck.needs_transliteration is set) --
    # left null otherwise rather than the LLM guessing one up for a
    # language that doesn't use a non-Latin script.
    transliteration: str | None = None
    example_sentence: str
    example_sentence_translation: str
    example_sentence_transliteration: str | None = None


async def generate_card_from_word(
    llm: LLMProvider,
    target_language_name: str,
    base_language_name: str,
    base_word: str,
    transliteration_label: str | None = None,
) -> GeneratedCard:
    transliteration_clause = (
        f"\n- transliteration: the {transliteration_label} (romanization) of "
        "target_text"
        f"\n- example_sentence_transliteration: the {transliteration_label} of "
        "example_sentence"
        if transliteration_label
        else ""
    )
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
        f"translation{transliteration_clause}"
    )
    return await llm.generate_structured(prompt, GeneratedCard, model_tier="fast")


class GeneratedTransliteration(BaseModel):
    transliteration: str
    # Null when the note being backfilled has no example_sentence to
    # transliterate in the first place -- see backfill_transliteration.py.
    example_sentence_transliteration: str | None = None


async def generate_transliteration(
    llm: LLMProvider,
    target_language_name: str,
    transliteration_label: str,
    target_text: str,
    example_sentence: str | None,
) -> GeneratedTransliteration:
    """Backs `backfill_transliteration.py` -- fills in the transliteration
    for a note that already exists (created before this field was
    generated, or added via the plain manual quick-add form without one),
    rather than generating a brand new card from scratch.
    """
    example_clause = (
        f' Also give the {transliteration_label} of this example sentence that '
        f'uses the word: "{example_sentence}" -- return it as '
        "example_sentence_transliteration."
        if example_sentence
        else ""
    )
    prompt = (
        f"Give the {transliteration_label} (romanization) of the "
        f'{target_language_name} word "{target_text}" -- return it as '
        f"transliteration.{example_clause}"
    )
    return await llm.generate_structured(prompt, GeneratedTransliteration, model_tier="fast")
