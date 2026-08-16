import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, UUIDPkMixin
from app.models.enums import KnownVocabularySource, pg_enum


class KnownVocabularyItem(UUIDPkMixin, CreatedAtMixin, Base):
    """A passive, ungraded record that the user already knows a word --
    distinct from `VocabularyItem`, which is active Anki-deck content
    requiring a real translation and wired into TTS/example-generation.
    Populated either by the adaptive frequency-band placement check or by
    hand; never itself scheduled for review. See PLAN.md's 2026-08-14
    "Vocabulary -> Reading, known-vocabulary system" decision.

    `target_text` is stored lowercased regardless of input casing -- both
    the bundled placement-check word lists and manual-add input are
    normalized this way before insert. A deliberate simplification: unlike
    `VocabularyItem.target_text`, these rows have no display-typography
    requirement, so a plain lowercase `UniqueConstraint` is enough to dedupe
    a bulk placement-check save (which can insert hundreds of rows from a
    fixed dataset in one call) via `ON CONFLICT DO NOTHING` -- far cheaper
    at that volume than `VocabularyItem`'s accent/case-insensitive Python
    scan, which exists for low-volume, free-typed quick-add input instead.

    `source` starts as `PLACEMENT_CHECK` or `MANUAL` and flips to
    `PROMOTED` in place once the word becomes a real `VocabularyItem` +
    `Card` (see POST /known-vocabulary/{id}/promote) -- the row is kept,
    not deleted, so the known-words page can filter on it directly without
    cross-referencing the full `VocabularyItem` list on every render, and
    so a future content-generation feature can still count it as known.
    """

    __tablename__ = "known_vocabulary_items"
    __table_args__ = (UniqueConstraint("user_id", "course_id", "target_text"),)

    # Not nullable -- unlike VocabularyItem, there's no shared/curriculum
    # equivalent here: every known-vocabulary row is inherently one user's
    # self-report or placement-check estimate.
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False, index=True
    )
    target_text: Mapped[str] = mapped_column(String(500), nullable=False)
    source: Mapped[KnownVocabularySource] = mapped_column(
        pg_enum(KnownVocabularySource, length=20), nullable=False
    )

    def __repr__(self) -> str:
        return f"<KnownVocabularyItem {self.target_text!r} ({self.source})>"
