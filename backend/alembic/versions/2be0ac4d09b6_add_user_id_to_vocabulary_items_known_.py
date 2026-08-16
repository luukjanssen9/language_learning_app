"""add user_id to vocabulary_items, known_vocabulary_items, reading_passages

Revision ID: 2be0ac4d09b6
Revises: 839c4855cdeb
Create Date: 2026-08-15 15:37:58.086512

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2be0ac4d09b6"
down_revision: str | Sequence[str] | None = "839c4855cdeb"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # All three columns start nullable -- even known_vocabulary_items/
    # reading_passages, whose model declares user_id NOT NULL -- so the
    # backfill below has something to fill in before the NOT NULL
    # constraints go on. vocabulary_items.user_id stays nullable
    # permanently (NULL = shared curriculum content, see the model's
    # docstring).
    op.add_column("vocabulary_items", sa.Column("user_id", sa.UUID(), nullable=True))
    op.create_index(
        op.f("ix_vocabulary_items_user_id"), "vocabulary_items", ["user_id"], unique=False
    )
    op.create_foreign_key(None, "vocabulary_items", "users", ["user_id"], ["id"])

    op.add_column("known_vocabulary_items", sa.Column("user_id", sa.UUID(), nullable=True))
    op.create_index(
        op.f("ix_known_vocabulary_items_user_id"),
        "known_vocabulary_items",
        ["user_id"],
        unique=False,
    )
    op.create_foreign_key(None, "known_vocabulary_items", "users", ["user_id"], ["id"])

    op.add_column("reading_passages", sa.Column("user_id", sa.UUID(), nullable=True))
    op.create_index(
        op.f("ix_reading_passages_user_id"), "reading_passages", ["user_id"], unique=False
    )
    op.create_foreign_key(None, "reading_passages", "users", ["user_id"], ["id"])

    # Backfill to the oldest User row rather than a hardcoded id -- portable
    # to a genuinely empty DB (the subquery returns NULL, every UPDATE
    # touches zero rows, and NOT NULL on an empty table is trivially safe)
    # instead of being specific to this one dev database.
    #
    # vocabulary_items: excludes any row referenced by
    # lesson_exercise_vocabulary -- those are shared curriculum content
    # (e.g. the seeded Greetings/Family skill vocab), not this user's
    # personal data, and must stay NULL.
    op.execute(
        """
        UPDATE vocabulary_items
        SET user_id = (SELECT id FROM users ORDER BY created_at LIMIT 1)
        WHERE user_id IS NULL
          AND id NOT IN (SELECT DISTINCT vocabulary_item_id FROM lesson_exercise_vocabulary)
        """
    )
    op.execute(
        """
        UPDATE known_vocabulary_items
        SET user_id = (SELECT id FROM users ORDER BY created_at LIMIT 1)
        WHERE user_id IS NULL
        """
    )
    op.execute(
        """
        UPDATE reading_passages
        SET user_id = (SELECT id FROM users ORDER BY created_at LIMIT 1)
        WHERE user_id IS NULL
        """
    )

    op.alter_column("known_vocabulary_items", "user_id", nullable=False)
    op.alter_column("reading_passages", "user_id", nullable=False)

    op.drop_constraint(
        op.f("known_vocabulary_items_course_id_target_text_key"),
        "known_vocabulary_items",
        type_="unique",
    )
    op.create_unique_constraint(
        None, "known_vocabulary_items", ["user_id", "course_id", "target_text"]
    )
    # NOTE: autogenerate also detected a pre-existing 'ix_cards_due_at'
    # index drop here -- unrelated schema drift from before this migration
    # (superseded by the composite ix_cards_deck_id_due_at, never cleaned
    # up), deliberately left out to keep this migration scoped to auth only.


def downgrade() -> None:
    op.drop_constraint(None, "known_vocabulary_items", type_="unique")
    op.create_unique_constraint(
        op.f("known_vocabulary_items_course_id_target_text_key"),
        "known_vocabulary_items",
        ["course_id", "target_text"],
    )

    op.drop_constraint(None, "reading_passages", type_="foreignkey")
    op.drop_index(op.f("ix_reading_passages_user_id"), table_name="reading_passages")
    op.drop_column("reading_passages", "user_id")

    op.drop_constraint(None, "known_vocabulary_items", type_="foreignkey")
    op.drop_index(op.f("ix_known_vocabulary_items_user_id"), table_name="known_vocabulary_items")
    op.drop_column("known_vocabulary_items", "user_id")

    op.drop_constraint(None, "vocabulary_items", type_="foreignkey")
    op.drop_index(op.f("ix_vocabulary_items_user_id"), table_name="vocabulary_items")
    op.drop_column("vocabulary_items", "user_id")
