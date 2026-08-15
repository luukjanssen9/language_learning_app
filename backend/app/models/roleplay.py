import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, UUIDPkMixin
from app.models.enums import MessageRole, pg_enum


class RoleplayScenario(UUIDPkMixin, CreatedAtMixin, Base):
    """A pre-authored roleplay situation (e.g. "order coffee"), shared
    across every course/language -- unlike `Skill`, deliberately NOT
    course-scoped: the situation itself doesn't vary by target language,
    only the language a given `Conversation` conducts it in does. Avoids
    seeding the same scenario once per course.
    """

    __tablename__ = "roleplay_scenarios"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    # Instructs the LLM: persona, situation, goal. Written once in plain
    # English, reused verbatim for every target language.
    setup_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    def __repr__(self) -> str:
        return f"<RoleplayScenario {self.slug!r}>"


class Conversation(UUIDPkMixin, CreatedAtMixin, Base):
    """One roleplay chat session. Accumulates `ConversationMessage` rows
    over time, per-course -- same "many rows, each a persisted snapshot"
    shape as `ReadingPassage`/`JournalEntry`.
    """

    __tablename__ = "conversations"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False, index=True
    )
    scenario_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("roleplay_scenarios.id"), nullable=False, index=True
    )

    def __repr__(self) -> str:
        return f"<Conversation {self.id} course={self.course_id}>"


class ConversationMessage(UUIDPkMixin, CreatedAtMixin, Base):
    """One turn in a `Conversation`. Ordered by `created_at`, no separate
    `order_index` needed -- turns are always appended, never reordered.
    """

    __tablename__ = "conversation_messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True
    )
    role: Mapped[MessageRole] = mapped_column(pg_enum(MessageRole, length=20), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    # list[{"original": str, "corrected": str, "explanation": str}] -- only
    # ever set on role=USER rows, same shape as JournalEntry.corrections.
    # Null (not an empty list) for ASSISTANT rows, where "no corrections"
    # doesn't apply at all, and for a USER row before grading completes.
    corrections: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<ConversationMessage {self.id} role={self.role}>"
