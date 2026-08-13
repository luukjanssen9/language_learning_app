import uuid

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, UUIDPkMixin


class Skill(UUIDPkMixin, CreatedAtMixin, Base):
    """A lesson unit within a course (Duolingo-style 'skill')."""

    __tablename__ = "skills"
    __table_args__ = (UniqueConstraint("course_id", "slug", name="uq_skill_course_slug"),)

    course_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    prerequisite_skill_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("skills.id"), nullable=True, index=True
    )
    # Tags a skill as belonging to a named per-language specialty module
    # (e.g. "spanish-verb-conjugation"), not a code branch -- NULL for
    # ordinary vocab skills, which is most of them.
    specialty_module: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # Ungraded teaching content shown once before this skill's practice
    # queue starts: {"explanation": str, "examples": [{"target_text": str,
    # "base_text": str}, ...]}. NULL for skills with no intro (the norm).
    intro_content: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<Skill {self.slug!r}>"
