"""Pure unit tests for note-to-card generation -- no DB, no HTTP client.
`Language` is constructed directly in memory, same convention as
test_exercise_grading.py's `LessonExercise` construction.
"""

import uuid

from app.models.enums import CardDirection, CardState
from app.models.language import Language
from app.services.note_cards import build_cards_for_note


def _language(grammar_config: dict) -> Language:
    return Language(code="xx", name="Test Language", grammar_config=grammar_config)


def test_single_direction_language_produces_one_recognition_card():
    spanish = _language({"vocab_deck": {"dual_direction_cards": False}})
    deck_id = uuid.uuid4()
    vocab_id = uuid.uuid4()

    cards = build_cards_for_note(deck_id, vocab_id, spanish)

    assert len(cards) == 1
    assert cards[0].deck_id == deck_id
    assert cards[0].vocabulary_item_id == vocab_id
    assert cards[0].direction == CardDirection.TARGET_TO_BASE
    assert cards[0].state == CardState.NEW


def test_missing_vocab_deck_config_defaults_to_single_card():
    # A language with no "vocab_deck" key at all (e.g. any language
    # config predating this feature) shouldn't crash or accidentally get
    # a production card it never asked for.
    no_config_language = _language({})

    cards = build_cards_for_note(uuid.uuid4(), uuid.uuid4(), no_config_language)

    assert len(cards) == 1
    assert cards[0].direction == CardDirection.TARGET_TO_BASE


def test_dual_direction_language_produces_recognition_and_suspended_production():
    chinese = _language({"vocab_deck": {"dual_direction_cards": True}})
    deck_id = uuid.uuid4()
    vocab_id = uuid.uuid4()

    cards = build_cards_for_note(deck_id, vocab_id, chinese)

    assert len(cards) == 2
    recognition, production = cards
    assert recognition.direction == CardDirection.TARGET_TO_BASE
    assert recognition.state == CardState.NEW
    assert production.direction == CardDirection.BASE_TO_TARGET
    assert production.state == CardState.SUSPENDED
    # Both cards belong to the same note and deck -- that's what lets
    # list_due_cards find the recognition card as the production card's
    # "sibling" purely from vocabulary_item_id + direction, no extra FK.
    assert recognition.vocabulary_item_id == production.vocabulary_item_id == vocab_id
    assert recognition.deck_id == production.deck_id == deck_id
