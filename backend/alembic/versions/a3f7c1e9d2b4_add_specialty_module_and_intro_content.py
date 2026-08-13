"""add specialty_module and intro_content for Phase 4

Revision ID: a3f7c1e9d2b4
Revises: 1c5e3053476f
Create Date: 2026-08-13 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a3f7c1e9d2b4"
down_revision: str | Sequence[str] | None = "1c5e3053476f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("skills", sa.Column("specialty_module", sa.String(length=50), nullable=True))
    op.add_column(
        "skills", sa.Column("intro_content", postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )
    op.add_column(
        "lesson_exercises",
        sa.Column("specialty_module", sa.String(length=50), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("lesson_exercises", "specialty_module")
    op.drop_column("skills", "intro_content")
    op.drop_column("skills", "specialty_module")
