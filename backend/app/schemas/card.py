import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.enums import CardDirection, CardState, ReviewRating
from app.schemas.review_log import ReviewLogRead
from app.schemas.vocabulary import VocabularyItemRead


class CardBase(BaseModel):
    deck_id: uuid.UUID
    vocabulary_item_id: uuid.UUID | None = None
    front_override: str | None = None
    back_override: str | None = None
    direction: CardDirection = CardDirection.TARGET_TO_BASE


class CardCreate(CardBase):
    pass


class CardUpdate(BaseModel):
    front_override: str | None = None
    back_override: str | None = None
    direction: CardDirection | None = None


class CardRead(CardBase):
    """FSRS scheduling fields are read-only here — they're written by the
    review-submission endpoint, not this basic CRUD surface.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    state: CardState
    step: int | None
    stability: float | None
    difficulty: float | None
    due_at: datetime | None
    reps: int
    lapses: int
    last_reviewed_at: datetime | None
    # Populated via selectinload(Card.vocabulary_item) wherever a route
    # returns cards -- lets Flashcard.tsx render vocabulary-backed cards
    # without a separate per-card fetch (a due-queue response can hold
    # ~100+ cards). None for override-only cards, which is most of the
    # ones created before this feature existed.
    vocabulary_item: VocabularyItemRead | None = None


class CardQuickAdd(BaseModel):
    """Request body for POST /cards/quick-add -- creates one VocabularyItem
    ("note") plus the Card(s) it produces (one, or two for a language with
    `vocab_deck.dual_direction_cards`) in a single round trip, the whole
    point of "capture a card mid-shadowing-session" rather than a
    multi-step flow. See app/services/note_cards.py for the card-count
    logic and PLAN.md's 2026-08-14 "Anki-style vocab decks" decision.
    """

    deck_id: uuid.UUID
    target_text: str
    base_text: str
    part_of_speech: str | None = None
    source: str | None = None
    example_sentence: str | None = None
    example_sentence_translation: str | None = None
    tags: list[str] = []
    attributes: dict = {}


class CardQuickAddResponse(BaseModel):
    vocabulary_item: VocabularyItemRead
    cards: list[CardRead]


class CardReviewSubmit(BaseModel):
    """Request body for POST /cards/{card_id}/review.

    `reviewed_at` is normally omitted — the server uses the current time.
    It's exposed deliberately, not just for tests: the FSRS scheduler
    itself already treats the review timestamp as a public parameter, and
    letting a client backdate a review has a real product shape too
    (logging a review done offline / on paper). The router enforces that
    it isn't in the future and doesn't precede the card's last review.
    """

    rating: ReviewRating
    reviewed_at: datetime | None = None

    @field_validator("reviewed_at")
    @classmethod
    def _reviewed_at_must_be_tz_aware(cls, v: datetime | None) -> datetime | None:
        if v is None:
            return None
        if v.tzinfo is None:
            raise ValueError("reviewed_at must be timezone-aware")
        return v.astimezone(UTC)


class CardReviewResponse(BaseModel):
    """Bundles the updated card with the review-log row it produced, so a
    client showing "next review in N days" alongside a confirmation of
    what was logged doesn't need a second round trip for data that's
    already in memory after the same commit.
    """

    card: CardRead
    review_log: ReviewLogRead
