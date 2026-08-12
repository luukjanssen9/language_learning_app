import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, CreatedAtMixin, UUIDPkMixin
from app.models.language import Language


class Course(UUIDPkMixin, CreatedAtMixin, Base):
    """A base-language -> target-language pairing, e.g. English -> Spanish.

    Adding a new language pair later is a new row here (plus new `Language`
    rows if needed), not a schema or code change.
    """

    __tablename__ = "courses"
    __table_args__ = (
        UniqueConstraint("base_language_id", "target_language_id", name="uq_course_language_pair"),
    )

    base_language_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("languages.id"), nullable=False, index=True
    )
    target_language_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("languages.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    base_language: Mapped["Language"] = relationship(foreign_keys=[base_language_id])
    target_language: Mapped["Language"] = relationship(foreign_keys=[target_language_id])

    def __repr__(self) -> str:
        return f"<Course {self.slug}>"
