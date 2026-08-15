"""add vocabulary_examples.mnemonic

Revision ID: d8e4f21a9c6b
Revises: aa19600096db
Create Date: 2026-08-15 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d8e4f21a9c6b"
down_revision: str | Sequence[str] | None = "aa19600096db"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("vocabulary_examples", sa.Column("mnemonic", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("vocabulary_examples", "mnemonic")
