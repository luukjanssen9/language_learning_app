import uuid

from sqlalchemy import ForeignKey, LargeBinary, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, UUIDPkMixin


class VocabularyAudio(UUIDPkMixin, CreatedAtMixin, Base):
    """A TTS-generated pronunciation clip for a `VocabularyItem`'s
    `target_text`, cached once generated so a given word only ever costs
    one real Google Cloud Text-to-Speech call, not one per playback --
    see PLAN.md's 2026-08-14 "TTS audio for vocab cards" decision.

    Unlike `VocabularyExample` (several LLM-generated sentences per
    item), a word has exactly one canonical pronunciation -- `unique=True`
    enforces one row per item at the DB level, not just by convention.
    """

    __tablename__ = "vocabulary_audio"

    vocabulary_item_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("vocabulary_items.id"),
        nullable=False,
        unique=True,
        index=True,
    )
    audio_data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)

    def __repr__(self) -> str:
        return f"<VocabularyAudio vocabulary_item_id={self.vocabulary_item_id}>"
