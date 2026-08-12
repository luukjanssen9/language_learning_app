import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, UUIDPkMixin


class UserProgress(UUIDPkMixin, CreatedAtMixin, Base):
    """Per-user, per-skill mastery tracking.

    `streak_count` is reserved but unused by any v1 UI, per the minimal-
    gamification decision in PLAN.md — kept here so adding streak UI later
    doesn't require a migration.
    """

    __tablename__ = "user_progress"
    __table_args__ = (UniqueConstraint("user_id", "skill_id", name="uq_user_progress_skill"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("skills.id"), nullable=False, index=True
    )
    mastery_level: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    last_practiced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    times_correct: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    times_attempted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    streak_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        return f"<UserProgress user={self.user_id} skill={self.skill_id}>"
