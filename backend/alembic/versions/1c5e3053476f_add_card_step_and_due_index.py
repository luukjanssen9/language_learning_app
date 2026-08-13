"""add card.step and composite (deck_id, due_at) index

Revision ID: 1c5e3053476f
Revises: 1d5df3c16c8d
Create Date: 2026-08-12 18:05:50.309043

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1c5e3053476f"
down_revision: str | Sequence[str] | None = "1d5df3c16c8d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("cards", sa.Column("step", sa.Integer(), nullable=True))
    op.drop_index(op.f("ix_cards_deck_id"), table_name="cards")
    op.create_index(op.f("ix_cards_deck_id_due_at"), "cards", ["deck_id", "due_at"])


def downgrade() -> None:
    op.drop_index(op.f("ix_cards_deck_id_due_at"), table_name="cards")
    op.create_index(op.f("ix_cards_deck_id"), "cards", ["deck_id"])
    op.drop_column("cards", "step")
