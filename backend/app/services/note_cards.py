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
"""

import uuid

from app.models.card import Card
from app.models.enums import CardDirection, CardState
from app.models.language import Language


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
