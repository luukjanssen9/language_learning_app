import uuid

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
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

    def __repr__(self) -> str:
        return f"<Skill {self.slug!r}>"
