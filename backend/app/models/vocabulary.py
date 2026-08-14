import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, UUIDPkMixin


class VocabularyItem(UUIDPkMixin, CreatedAtMixin, Base):
    """A canonical dictionary entry, shared by flashcards and lesson exercises
    so word content isn't duplicated across the two systems.

    `attributes` holds grammatical metadata (gender, conjugation class,
    register, transliteration like pinyin, ...) as a generic bag rather than
    dedicated columns, since not every language has the same grammatical
    categories -- see PLAN.md's 2026-08-14 "Anki-style vocab decks" decision.

    `source`/`example_sentence`/`example_sentence_translation` hold a real
    sentence this word was actually encountered in (shadowing transcripts,
    shows, reading) plus where -- distinct from `VocabularyExample`
    (app/models/vocabulary_example.py), which holds LLM-generated practice
    sentences with no provenance. Both coexist; this one is authoritative,
    that one is supplementary.
    """

    __tablename__ = "vocabulary_items"

    course_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False, index=True
    )
    target_text: Mapped[str] = mapped_column(String(500), nullable=False)
    base_text: Mapped[str] = mapped_column(String(500), nullable=False)
    part_of_speech: Mapped[str | None] = mapped_column(String(50), nullable=True)
    attributes: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    source: Mapped[str | None] = mapped_column(String(300), nullable=True)
    example_sentence: Mapped[str | None] = mapped_column(Text, nullable=True)
    example_sentence_translation: Mapped[str | None] = mapped_column(Text, nullable=True)
    # A list[str], stored as JSONB rather than a native Postgres array --
    # matches `attributes`' existing JSONB-bag convention; no array-typed
    # column exists yet elsewhere in this schema to justify that type instead.
    tags: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)

    def __repr__(self) -> str:
        return f"<VocabularyItem {self.target_text!r} -> {self.base_text!r}>"
