import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, UUIDPkMixin


class VocabularyItem(UUIDPkMixin, CreatedAtMixin, Base):
    """A canonical dictionary entry, shared by flashcards and lesson exercises
    so word content isn't duplicated across the two systems.

    `attributes` holds grammatical metadata (gender, conjugation class,
    register, ...) as a generic bag rather than dedicated columns, since not
    every language has the same grammatical categories.
    """

    __tablename__ = "vocabulary_items"

    course_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False, index=True
    )
    target_text: Mapped[str] = mapped_column(String(500), nullable=False)
    base_text: Mapped[str] = mapped_column(String(500), nullable=False)
    part_of_speech: Mapped[str | None] = mapped_column(String(50), nullable=True)
    attributes: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    def __repr__(self) -> str:
        return f"<VocabularyItem {self.target_text!r} -> {self.base_text!r}>"
