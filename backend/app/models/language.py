from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, UUIDPkMixin
from app.models.enums import ScriptDirection, pg_enum


class Language(UUIDPkMixin, CreatedAtMixin, Base):
    """A language config row — never a code branch.

    `grammar_config` holds per-language rules (conjugation classes, gender
    system, pluralization, etc.) that app logic reads at runtime instead of
    hardcoding per-language behavior.
    """

    __tablename__ = "languages"

    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    script_direction: Mapped[ScriptDirection] = mapped_column(
        pg_enum(ScriptDirection, length=10),
        default=ScriptDirection.LTR,
        nullable=False,
    )
    grammar_config: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    def __repr__(self) -> str:
        return f"<Language {self.code}>"
