import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, UUIDPkMixin
from app.models.enums import CardDirection, CardState, pg_enum


class Card(UUIDPkMixin, CreatedAtMixin, Base):
    """An SRS-scheduled flashcard. Current FSRS state lives on the row;
    `ReviewLog` holds the append-only history used to tune scheduling.
    """

    __tablename__ = "cards"

    deck_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("decks.id"), nullable=False, index=True
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

    # --- FSRS scheduling state ---
    state: Mapped[CardState] = mapped_column(
        pg_enum(CardState, length=20),
        default=CardState.NEW,
        nullable=False,
    )
    stability: Mapped[float | None] = mapped_column(Float, nullable=True)
    difficulty: Mapped[float | None] = mapped_column(Float, nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    reps: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    lapses: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<Card {self.id} state={self.state}>"
