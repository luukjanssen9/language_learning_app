import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPkMixin
from app.models.enums import CardState, ReviewRating, pg_enum


class ReviewLog(UUIDPkMixin, Base):
    """Append-only history of card reviews — used for the due-card queue's
    audit trail and for tuning FSRS parameters later, not just scheduling.
    """

    __tablename__ = "review_logs"

    card_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("cards.id"), nullable=False, index=True
    )
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    rating: Mapped[ReviewRating] = mapped_column(pg_enum(ReviewRating, length=10), nullable=False)
    elapsed_days: Mapped[float | None] = mapped_column(Float, nullable=True)
    scheduled_days: Mapped[float | None] = mapped_column(Float, nullable=True)
    state_before: Mapped[CardState | None] = mapped_column(
        pg_enum(CardState, length=20), nullable=True
    )

    def __repr__(self) -> str:
        return f"<ReviewLog card={self.card_id} rating={self.rating}>"
