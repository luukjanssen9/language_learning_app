import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, UUIDPkMixin
from app.models.enums import CardDirection, CardState, pg_enum


class Card(UUIDPkMixin, CreatedAtMixin, Base):
    """An SRS-scheduled flashcard. Current FSRS state lives on the row;
    `ReviewLog` holds the append-only history used to tune scheduling.
    """

    __tablename__ = "cards"
    __table_args__ = (
        # The due-card queue always filters deck_id + due_at together (see
        # api/routes/cards.py's list_due_cards); this also serves plain
        # deck_id-only lookups as a leading-column prefix, so there's no
        # separate single-column deck_id index.
        Index("ix_cards_deck_id_due_at", "deck_id", "due_at"),
    )

    deck_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("decks.id"), nullable=False
    )
    vocabulary_item_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("vocabulary_items.id"), nullable=True, index=True
    )

    # Only needed for cards not derived from a VocabularyItem, or to override
    # the shared vocab entry's text for this specific card.
    front_override: Mapped[str | None] = mapped_column(Text, nullable=True)
    back_override: Mapped[str | None] = mapped_column(Text, nullable=True)

    direction: Mapped[CardDirection] = mapped_column(
        pg_enum(CardDirection, length=20),
        default=CardDirection.TARGET_TO_BASE,
        nullable=False,
    )

    # --- FSRS scheduling state --- (field order mirrors fsrs.Card's own
    # state/step/stability/difficulty/due/last_review ordering)
    state: Mapped[CardState] = mapped_column(
        pg_enum(CardState, length=20),
        default=CardState.NEW,
        nullable=False,
    )
    # Same-day learning/relearning step counter (index into the FSRS
    # scheduler's learning_steps/relearning_steps) — None once a card has
    # graduated to Review and has no notion of "steps" anymore.
    step: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stability: Mapped[float | None] = mapped_column(Float, nullable=True)
    difficulty: Mapped[float | None] = mapped_column(Float, nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reps: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    lapses: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<Card {self.id} state={self.state}>"
