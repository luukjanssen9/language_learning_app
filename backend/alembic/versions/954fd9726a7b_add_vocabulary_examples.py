"""add vocabulary_examples table

Revision ID: 954fd9726a7b
Revises: a3f7c1e9d2b4
Create Date: 2026-08-13 23:27:35.436830

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "954fd9726a7b"
down_revision: str | Sequence[str] | None = "a3f7c1e9d2b4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "vocabulary_examples",
        sa.Column("vocabulary_item_id", sa.UUID(), nullable=False),
        sa.Column("target_text", sa.String(length=500), nullable=False),
        sa.Column("base_text", sa.String(length=500), nullable=False),
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
        op.f("ix_vocabulary_examples_vocabulary_item_id"),
        "vocabulary_examples",
        ["vocabulary_item_id"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_vocabulary_examples_vocabulary_item_id"), table_name="vocabulary_examples"
    )
    op.drop_table("vocabulary_examples")
