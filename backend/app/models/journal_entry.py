import uuid

from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, UUIDPkMixin


class JournalEntry(UUIDPkMixin, CreatedAtMixin, Base):
    """A user's free-form writing in the target language, plus the LLM
    correction it produced -- see PLAN.md's 2026-08-14 "Journal
    correction" decision.

    The correction result is a one-time snapshot of what was actually
    submitted, not something re-derivable from a static prompt the way
    `LessonExercise.prompt` is -- stored directly rather than recomputed
    on read.
    """

    __tablename__ = "journal_entries"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False, index=True
    )
    submitted_text: Mapped[str] = mapped_column(Text, nullable=False)
    corrected_text: Mapped[str] = mapped_column(Text, nullable=False)
    overall_feedback: Mapped[str] = mapped_column(Text, nullable=False)
    # list[{"original": str, "corrected": str, "explanation": str}]
    corrections: Mapped[list] = mapped_column(JSONB, nullable=False)
    # list[{"target_text": str, "base_text": str, "example_sentence": str}] --
    # words used *correctly*; misused vocab stays inside `corrections` only,
    # per the 2026-08-14 decision (a conjugation slip isn't a new card).
    vocabulary_suggestions: Mapped[list] = mapped_column(JSONB, nullable=False)

    def __repr__(self) -> str:
        return f"<JournalEntry {self.id} user={self.user_id}>"
