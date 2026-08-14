"""add note fields, suspended card state, daily new-card cap

Revision ID: 2ca978d0bc82
Revises: 954fd9726a7b
Create Date: 2026-08-14 00:24:21.877458

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2ca978d0bc82"
down_revision: str | Sequence[str] | None = "954fd9726a7b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("decks", sa.Column("daily_new_card_cap", sa.Integer(), nullable=True))
    op.add_column("vocabulary_items", sa.Column("source", sa.String(length=300), nullable=True))
    op.add_column("vocabulary_items", sa.Column("example_sentence", sa.Text(), nullable=True))
    op.add_column(
        "vocabulary_items", sa.Column("example_sentence_translation", sa.Text(), nullable=True)
    )
    op.add_column(
        "vocabulary_items",
        sa.Column(
            "tags",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
    )
    # The server_default above is only needed to backfill existing rows on
    # this ALTER -- the ORM model already supplies default=list for every
    # future INSERT, matching how `attributes` (JSONB, default=dict) has no
    # server_default either. Dropped once existing rows are backfilled so
    # the two stay consistent.
    op.alter_column("vocabulary_items", "tags", server_default=None)
    # CardState.SUSPENDED needs no DDL: the column is plain VARCHAR
    # (native_enum=False, see app/models/enums.py's pg_enum()), so a new
    # member is a Python-only change, not an ALTER TYPE.


def downgrade() -> None:
    op.drop_column("vocabulary_items", "tags")
    op.drop_column("vocabulary_items", "example_sentence_translation")
    op.drop_column("vocabulary_items", "example_sentence")
    op.drop_column("vocabulary_items", "source")
    op.drop_column("decks", "daily_new_card_cap")
