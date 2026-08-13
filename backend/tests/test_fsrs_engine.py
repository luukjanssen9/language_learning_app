"""Pure unit tests for the FSRS service layer -- no DB, no HTTP client.
`Card` instances are constructed directly in memory (never flushed to a
session), and `apply_review` is called directly.

These assert on *our* code's behavior (state transitions, our own computed
fields, reps/lapses bookkeeping, NEW-state handling) -- never on FSRS's
exact interval magnitudes. The scheduler runs with its default
`enable_fuzzing=True`, so asserting an exact post-graduation `due_at` would
be flaky by design; where a value is FSRS-computed we assert relationships
(e.g. `due_at > reviewed_at`) instead of fixed numbers.
"""

from datetime import UTC, datetime, timedelta

import pytest

from app.models.card import Card
from app.models.enums import CardState, ReviewRating
from app.services.fsrs_engine import apply_review

T0 = datetime(2026, 1, 1, tzinfo=UTC)


def _new_card() -> Card:
    # reps/lapses default to 0 only at DB-insert time (mapped_column's
    # `default=`); a plain in-memory Card() never touches a session, so
    # they must be set explicitly or apply_review's `card.reps += 1`
    # would fail against None.
    return Card(state=CardState.NEW, reps=0, lapses=0)


def test_new_card_first_good_review_enters_learning_step_one():
    card = _new_card()
    outcome = apply_review(card, ReviewRating.GOOD, T0)

    assert card.state == CardState.LEARNING
    assert card.step == 1  # default learning_steps has 2 entries -- not graduated yet
    assert card.stability is not None
    assert card.difficulty is not None
    assert card.due_at is not None
    assert card.due_at > T0
    assert card.reps == 1
    assert card.lapses == 0
    assert outcome.state_before == CardState.NEW
    assert outcome.elapsed_days is None
    assert outcome.is_lapse is False


def test_new_card_first_easy_review_graduates_directly_to_review():
    card = _new_card()
    apply_review(card, ReviewRating.EASY, T0)

    assert card.state == CardState.REVIEW
    assert card.step is None
    assert card.reps == 1


def test_second_good_review_after_first_step_graduates_to_review():
    card = _new_card()
    apply_review(card, ReviewRating.GOOD, T0)
    assert card.state == CardState.LEARNING
    assert card.step == 1

    t1 = T0 + timedelta(minutes=11)
    outcome = apply_review(card, ReviewRating.GOOD, t1)

    assert card.state == CardState.REVIEW
    assert card.step is None
    assert card.reps == 2
    assert outcome.elapsed_days == pytest.approx(11 / 1440)


def test_review_card_again_lapses_to_relearning_and_increments_lapses():
    card = _new_card()
    apply_review(card, ReviewRating.EASY, T0)  # graduate straight to Review
    assert card.state == CardState.REVIEW

    t1 = T0 + timedelta(days=5)
    outcome = apply_review(card, ReviewRating.AGAIN, t1)

    assert card.state == CardState.RELEARNING
    assert card.step == 0
    assert card.lapses == 1
    assert outcome.is_lapse is True
    assert outcome.state_before == CardState.REVIEW


def test_relearning_good_review_graduates_back_without_double_counting_lapse():
    card = _new_card()
    apply_review(card, ReviewRating.EASY, T0)  # -> Review
    t1 = T0 + timedelta(days=5)
    apply_review(card, ReviewRating.AGAIN, t1)  # -> Relearning, lapses=1
    assert card.lapses == 1

    t2 = t1 + timedelta(minutes=11)
    outcome = apply_review(card, ReviewRating.GOOD, t2)

    assert card.state == CardState.REVIEW
    assert card.lapses == 1  # unchanged -- this review's state_before was Relearning, not Review
    assert outcome.is_lapse is False
    assert outcome.state_before == CardState.RELEARNING


def test_elapsed_days_formula():
    card = _new_card()
    apply_review(card, ReviewRating.GOOD, T0)

    t1 = T0 + timedelta(days=3, hours=12)
    outcome = apply_review(card, ReviewRating.GOOD, t1)

    assert outcome.elapsed_days == pytest.approx(3.5)


def test_scheduled_days_formula_matches_resulting_due_at():
    card = _new_card()
    outcome = apply_review(card, ReviewRating.GOOD, T0)

    expected = (card.due_at - T0).total_seconds() / 86400
    assert outcome.scheduled_days == pytest.approx(expected)


@pytest.mark.parametrize(
    "rating", [ReviewRating.AGAIN, ReviewRating.HARD, ReviewRating.GOOD, ReviewRating.EASY]
)
def test_reps_increments_on_every_review_regardless_of_rating(rating: ReviewRating):
    card = _new_card()
    apply_review(card, rating, T0)

    assert card.reps == 1
