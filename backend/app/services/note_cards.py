"""Builds the `Card` row(s) a vocabulary note produces, from
`Language.grammar_config["vocab_deck"]`. Pure function, no DB access --
same convention as `conjugation.py`/`exercise_grading.py`; the caller
(route or seed script) is responsible for loading the target language and
persisting the returned cards.

Expected `grammar_config["vocab_deck"]` shape:
    {
      "dual_direction_cards": bool,
      "needs_transliteration": bool,       # only read by the frontend
      "transliteration_label": str,        # only read by the frontend
      "production_gate": {
        "min_successful_recognition_reviews": int,
        "min_days_since_note_added": int,
      },
    }

A language that omits "vocab_deck" entirely (or sets
`dual_direction_cards: False`) gets one card -- most languages, where
reading and producing the script isn't a distinct skill. One that sets it
`True` (e.g. Chinese, where recognizing hanzi and recalling them from
meaning alone are genuinely different skills) gets two: a recognition
card, immediately reviewable, and a production card that starts
`SUSPENDED` -- not yet eligible for the due-queue or the new-card cap --
until `list_due_cards` (app/api/routes/cards.py) unlocks it per the
`production_gate` config. See PLAN.md's 2026-08-14 "Anki-style vocab
decks" decision for the full reasoning.

`get_or_create_vocabulary_item_and_cards` below is a second, DB-touching
helper (unlike `build_cards_for_note`, not a pure function) -- the shared
core of `POST /cards/quick-add` and the known-vocabulary "promote"
endpoint, extracted once promotion became a second real caller of the
same resolve-or-create-note logic. See PLAN.md's 2026-08-14
"known-vocabulary system" decision.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.card import Card
from app.models.deck import Deck
from app.models.enums import CardDirection, CardState
from app.models.language import Language
from app.models.vocabulary import VocabularyItem
from app.services.text_normalize import normalize_for_comparison


def build_cards_for_note(
    deck_id: uuid.UUID, vocabulary_item_id: uuid.UUID, target_language: Language
) -> list[Card]:
    vocab_deck_config = target_language.grammar_config.get("vocab_deck", {})

    # `state` is set explicitly rather than relying on Card.state's
    # mapped_column default: that default only applies at INSERT time, not
    # at plain construction (same class of bug this project has hit
    # before with UserProgress's times_attempted/times_correct -- see
    # PLAN.md's Phase 4 Stage A decision log) -- and this function's
    # output is inspected directly by unit tests before ever being
    # flushed, not just by routes that immediately persist it.
    recognition = Card(
        deck_id=deck_id,
        vocabulary_item_id=vocabulary_item_id,
        direction=CardDirection.TARGET_TO_BASE,
        state=CardState.NEW,
    )
    if not vocab_deck_config.get("dual_direction_cards", False):
        return [recognition]

    production = Card(
        deck_id=deck_id,
        vocabulary_item_id=vocabulary_item_id,
        direction=CardDirection.BASE_TO_TARGET,
        state=CardState.SUSPENDED,
    )
    return [recognition, production]


async def get_or_create_vocabulary_item_and_cards(
    db: AsyncSession,
    deck: Deck,
    target_language: Language,
    target_text: str,
    base_text: str,
    part_of_speech: str | None = None,
    source: str | None = None,
    example_sentence: str | None = None,
    example_sentence_translation: str | None = None,
    tags: list[str] | None = None,
    attributes: dict | None = None,
) -> tuple[VocabularyItem, list[Card]]:
    """Finds an existing `VocabularyItem` in `deck`'s course matching
    `(target_text, base_text)` (accent/case-insensitive, same identity
    `quick_add_card` originally used), or creates one, then ensures `deck`
    has `Card`(s) for it via `build_cards_for_note`. Distinct senses of a
    homonym (different `base_text`) still get their own note. Does not
    commit -- the caller commits as part of its own transaction.
    """
    normalized_target = normalize_for_comparison(target_text)
    normalized_base = normalize_for_comparison(base_text)
    existing_items = await db.execute(
        select(VocabularyItem).where(VocabularyItem.course_id == deck.course_id)
    )
    vocabulary_item = next(
        (
            item
            for item in existing_items.scalars()
            if normalize_for_comparison(item.target_text) == normalized_target
            and normalize_for_comparison(item.base_text) == normalized_base
        ),
        None,
    )

    if vocabulary_item is None:
        vocabulary_item = VocabularyItem(
            course_id=deck.course_id,
            target_text=target_text,
            base_text=base_text,
            part_of_speech=part_of_speech,
            source=source,
            example_sentence=example_sentence,
            example_sentence_translation=example_sentence_translation,
            tags=tags or [],
            attributes=attributes or {},
        )
        db.add(vocabulary_item)
        await db.flush()
        cards = build_cards_for_note(deck.id, vocabulary_item.id, target_language)
        db.add_all(cards)
        return vocabulary_item, cards

    existing_cards = await db.execute(
        select(Card).where(Card.deck_id == deck.id, Card.vocabulary_item_id == vocabulary_item.id)
    )
    cards = list(existing_cards.scalars())
    if not cards:
        cards = build_cards_for_note(deck.id, vocabulary_item.id, target_language)
        db.add_all(cards)

    return vocabulary_item, cards
