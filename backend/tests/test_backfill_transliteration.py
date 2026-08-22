"""Unit tests for `_needs_backfill` (app/backfill_transliteration.py) --
pure function, no DB. Written after a real bug: the seeded Chinese vocab
batch (2026-08-14) has a word-level `transliteration` on every note but no
`example_sentence_transliteration`, and an earlier version of this
selection logic only checked the word half, silently skipping that entire
batch.
"""

from app.backfill_transliteration import _needs_backfill


def test_needs_backfill_when_word_transliteration_is_missing():
    assert _needs_backfill({}, None) is True
    assert _needs_backfill({}, "Some sentence.") is True


def test_does_not_need_backfill_when_fully_populated_and_no_example_sentence():
    assert _needs_backfill({"transliteration": "nǐ hǎo"}, None) is False


def test_needs_backfill_when_word_transliteration_present_but_sentence_missing():
    # The real seeded-data case this function's docstring calls out.
    assert _needs_backfill({"transliteration": "wèishénme"}, "你为什么迟到了？") is True


def test_does_not_need_backfill_when_both_are_already_populated():
    attributes = {
        "transliteration": "nǐ hǎo",
        "example_sentence_transliteration": "Nǐ hǎo!",
    }
    assert _needs_backfill(attributes, "你好！") is False
