"""add vocabulary_audio table

Revision ID: cfe4015d4aa5
Revises: 2ca978d0bc82
Create Date: 2026-08-14 02:29:49.605750

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "cfe4015d4aa5"
down_revision: str | Sequence[str] | None = "2ca978d0bc82"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "vocabulary_audio",
        sa.Column("vocabulary_item_id", sa.UUID(), nullable=False),
        sa.Column("audio_data", sa.LargeBinary(), nullable=False),
        sa.Column("content_type", sa.String(length=50), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["vocabulary_item_id"], ["vocabulary_items.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_vocabulary_audio_vocabulary_item_id"),
        "vocabulary_audio",
        ["vocabulary_item_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_vocabulary_audio_vocabulary_item_id"), table_name="vocabulary_audio"
    )
    op.drop_table("vocabulary_audio")
