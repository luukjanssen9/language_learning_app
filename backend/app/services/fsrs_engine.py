"""Translates between this app's `Card` ORM row (app/models/card.py) and
the `fsrs` PyPI package's own `Card`/`Scheduler` types, and writes the
result back onto the ORM row. This is the only module that imports `fsrs`
directly -- routers never touch the library's types.

Our `CardState` has one member the library has no concept of: `NEW`
("never reviewed"). Every other CardState member maps 1:1 onto the
library's `State` enum.
"""

from dataclasses import dataclass
from datetime import datetime

from fsrs import Card as FSRSCard
from fsrs import Rating as FSRSRating
from fsrs import Scheduler
from fsrs import State as FSRSState

from app.models.card import Card
from app.models.enums import CardState, ReviewRating

# Stateless and side-effect-free after construction (parameters/steps are
# fixed config, never mutated by review_card()), so one shared instance is
# safe across concurrent requests -- no per-request construction needed.
# Uses the library's own FSRS-6 default weights/steps; revisit if this ever
# needs to become configurable (e.g. a per-user desired_retention).
scheduler = Scheduler()

_STATE_TO_APP: dict[FSRSState, CardState] = {
    FSRSState.Learning: CardState.LEARNING,
    FSRSState.Review: CardState.REVIEW,
    FSRSState.Relearning: CardState.RELEARNING,
}
_APP_TO_FSRS_STATE: dict[CardState, FSRSState] = {v: k for k, v in _STATE_TO_APP.items()}

_RATING_TO_FSRS: dict[ReviewRating, FSRSRating] = {
    ReviewRating.AGAIN: FSRSRating.Again,
    ReviewRating.HARD: FSRSRating.Hard,
    ReviewRating.GOOD: FSRSRating.Good,
    ReviewRating.EASY: FSRSRating.Easy,
}


@dataclass(frozen=True, slots=True)
class ReviewOutcome:
    """What one `apply_review()` call computed, for the caller to persist
    onto a new `ReviewLog` row. (`apply_review` already writes the
    scheduling fields directly onto the `Card` it was given -- this is
    only the bookkeeping the `ReviewLog` table additionally needs.)
    """

    state_before: CardState
    elapsed_days: float | None
    scheduled_days: float
    is_lapse: bool


def _to_fsrs_card(card: Card) -> FSRSCard:
    """`card_id=0` always: we never read the library's own card_id (our
    UUID PK is authoritative), and passing an explicit id skips a
    time.sleep(0.001) the library does internally to avoid id collisions
    when auto-generating one -- pointless for us since we discard it.
    """
    if card.state == CardState.NEW:
        return FSRSCard(card_id=0)
    return FSRSCard(
        card_id=0,
        state=_APP_TO_FSRS_STATE[card.state],
        step=card.step,
        stability=card.stability,
        difficulty=card.difficulty,
        due=card.due_at,
        last_review=card.last_reviewed_at,
    )


def apply_review(card: Card, rating: ReviewRating, reviewed_at: datetime) -> ReviewOutcome:
    """Runs one FSRS review for `card` and mutates it in place with the
    resulting scheduling state (state, step, stability, difficulty,
    due_at, last_reviewed_at, reps, lapses). Pure computation: no DB
    session, no I/O -- the caller persists `card` and builds/saves the
    ReviewLog row from the returned ReviewOutcome.

    `reviewed_at` must be timezone-aware (the library raises ValueError
    otherwise) -- the router is responsible for that, via
    `CardReviewSubmit`'s field validator.
    """
    state_before = card.state
    fsrs_card = _to_fsrs_card(card)
    updated, _log = scheduler.review_card(
        fsrs_card, _RATING_TO_FSRS[rating], review_datetime=reviewed_at
    )
    # `_log` (the library's own ReviewLog) only carries rating +
    # review_datetime, both already known to us here -- discarded.

    elapsed_days = (
        (reviewed_at - card.last_reviewed_at).total_seconds() / 86400
        if card.last_reviewed_at is not None
        else None
    )
    scheduled_days = (updated.due - reviewed_at).total_seconds() / 86400
    # A "lapse" is a graduated card being forgotten, not any Again rating --
    # an Again on a still-Learning card is normal learning-phase friction.
    is_lapse = state_before == CardState.REVIEW and updated.state == FSRSState.Relearning

    card.state = _STATE_TO_APP[updated.state]
    card.step = updated.step
    card.stability = updated.stability
    card.difficulty = updated.difficulty
    card.due_at = updated.due
    card.last_reviewed_at = reviewed_at
    card.reps += 1
    if is_lapse:
        card.lapses += 1

    return ReviewOutcome(
        state_before=state_before,
        elapsed_days=elapsed_days,
        scheduled_days=scheduled_days,
        is_lapse=is_lapse,
    )
