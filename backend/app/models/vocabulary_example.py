import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, UUIDPkMixin


class VocabularyExample(UUIDPkMixin, CreatedAtMixin, Base):
    """An LLM-generated example sentence for a `VocabularyItem`, cached
    once generated (see `app/services/sentence_generation.py`) so a given
    vocabulary item only ever costs one real LLM call, not one per
    request -- the free-tier rate limit this project's Known Issues flag
    makes this worth doing from the start, not adding later.
    """

    __tablename__ = "vocabulary_examples"

    vocabulary_item_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("vocabulary_items.id"), nullable=False, index=True
    )
    target_text: Mapped[str] = mapped_column(String(500), nullable=False)
    base_text: Mapped[str] = mapped_column(String(500), nullable=False)
    # One mnemonic per *word*, not per example sentence -- generated once
    # alongside the batch of examples in the same LLM call and duplicated
    # onto each row rather than pulled into its own envelope/table, per
    # PLAN.md's "fold into the existing endpoint as an extra field" decision.
    # Nullable so pre-existing cached example rows (generated before this
    # field existed) degrade gracefully instead of needing a backfill --
    # they simply won't show a mnemonic until naturally regenerated.
    mnemonic: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<VocabularyExample {self.target_text!r}>"
