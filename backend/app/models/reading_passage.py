import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, UUIDPkMixin


class ReadingPassage(UUIDPkMixin, CreatedAtMixin, Base):
    """An LLM-generated short passage built from a course's known vocabulary
    (i+1: mostly known words, a handful of new ones), plus comprehension
    questions -- see PLAN.md's "reading passage generation" decision.

    Generated on demand (`POST /reading-passages`), not cached/keyed by a
    single row the way `VocabularyExample`/`VocabularyAudio` are -- a course
    can accumulate many passages over time, each a one-time snapshot of what
    was generated, like `JournalEntry`.
    """

    __tablename__ = "reading_passages"

    # Not nullable -- every passage is generated on demand for a specific
    # user's current known-vocabulary state, no shared/curriculum
    # equivalent (unlike VocabularyItem.user_id).
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False, index=True
    )
    target_text: Mapped[str] = mapped_column(Text, nullable=False)
    base_text: Mapped[str] = mapped_column(Text, nullable=False)
    # list[{"target_text": str, "base_text": str}] -- words the model
    # intentionally introduced beyond the known-word list it was given.
    new_vocabulary: Mapped[list] = mapped_column(JSONB, nullable=False)
    # list[{"question_text": str, "reference_answer": str}] --
    # reference_answer is never sent to the client (see ReadingPassageRead),
    # only read server-side to anchor the grading call.
    questions: Mapped[list] = mapped_column(JSONB, nullable=False)

    def __repr__(self) -> str:
        return f"<ReadingPassage {self.id} course={self.course_id}>"


class ReadingPassageAttempt(UUIDPkMixin, CreatedAtMixin, Base):
    """One graded answer to one `ReadingPassage` question. Field names
    (`is_correct`, `llm_feedback`) deliberately mirror `UserExerciseAttempt`
    -- same shape, different parent resource, so a later adaptive
    weak-point-targeting slice can read both uniformly.
    """

    __tablename__ = "reading_passage_attempts"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    reading_passage_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("reading_passages.id"), nullable=False, index=True
    )
    question_index: Mapped[int] = mapped_column(Integer, nullable=False)
    submitted_answer: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    llm_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<ReadingPassageAttempt passage={self.reading_passage_id} q={self.question_index}>"
