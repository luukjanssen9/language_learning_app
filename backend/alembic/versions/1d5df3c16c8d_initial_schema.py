"""initial schema

Revision ID: 1d5df3c16c8d
Revises:
Create Date: 2026-08-12 09:57:14.049694

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '1d5df3c16c8d'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "languages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=10), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("script_direction", sa.String(length=10), nullable=False),
        sa.Column("grammar_config", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    op.create_table(
        "courses",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("base_language_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_language_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["base_language_id"], ["languages.id"]),
        sa.ForeignKeyConstraint(["target_language_id"], ["languages.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
        sa.UniqueConstraint(
            "base_language_id", "target_language_id", name="uq_course_language_pair"
        ),
    )
    op.create_index(op.f("ix_courses_base_language_id"), "courses", ["base_language_id"])
    op.create_index(op.f("ix_courses_target_language_id"), "courses", ["target_language_id"])

    op.create_table(
        "decks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_decks_user_id"), "decks", ["user_id"])
    op.create_index(op.f("ix_decks_course_id"), "decks", ["course_id"])

    op.create_table(
        "skills",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=200), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("prerequisite_skill_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"]),
        sa.ForeignKeyConstraint(["prerequisite_skill_id"], ["skills.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("course_id", "slug", name="uq_skill_course_slug"),
    )
    op.create_index(op.f("ix_skills_course_id"), "skills", ["course_id"])
    op.create_index(op.f("ix_skills_prerequisite_skill_id"), "skills", ["prerequisite_skill_id"])

    op.create_table(
        "user_courses",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "course_id", name="uq_user_course"),
    )
    op.create_index(op.f("ix_user_courses_user_id"), "user_courses", ["user_id"])
    op.create_index(op.f("ix_user_courses_course_id"), "user_courses", ["course_id"])

    op.create_table(
        "vocabulary_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_text", sa.String(length=500), nullable=False),
        sa.Column("base_text", sa.String(length=500), nullable=False),
        sa.Column("part_of_speech", sa.String(length=50), nullable=True),
        sa.Column("attributes", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_vocabulary_items_course_id"), "vocabulary_items", ["course_id"])

    op.create_table(
        "cards",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("deck_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("vocabulary_item_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("front_override", sa.Text(), nullable=True),
        sa.Column("back_override", sa.Text(), nullable=True),
        sa.Column("direction", sa.String(length=20), nullable=False),
        sa.Column("state", sa.String(length=20), nullable=False),
        sa.Column("stability", sa.Float(), nullable=True),
        sa.Column("difficulty", sa.Float(), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reps", sa.Integer(), nullable=False),
        sa.Column("lapses", sa.Integer(), nullable=False),
        sa.Column("last_reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["deck_id"], ["decks.id"]),
        sa.ForeignKeyConstraint(["vocabulary_item_id"], ["vocabulary_items.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_cards_deck_id"), "cards", ["deck_id"])
    op.create_index(op.f("ix_cards_vocabulary_item_id"), "cards", ["vocabulary_item_id"])
    op.create_index(op.f("ix_cards_due_at"), "cards", ["due_at"])

    op.create_table(
        "review_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("card_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "reviewed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("rating", sa.String(length=10), nullable=False),
        sa.Column("elapsed_days", sa.Float(), nullable=True),
        sa.Column("scheduled_days", sa.Float(), nullable=True),
        sa.Column("state_before", sa.String(length=20), nullable=True),
        sa.ForeignKeyConstraint(["card_id"], ["cards.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_review_logs_card_id"), "review_logs", ["card_id"])

    op.create_table(
        "lesson_exercises",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("exercise_type", sa.String(length=20), nullable=False),
        sa.Column("prompt", postgresql.JSONB(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_lesson_exercises_skill_id"), "lesson_exercises", ["skill_id"])

    op.create_table(
        "lesson_exercise_vocabulary",
        sa.Column("lesson_exercise_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("vocabulary_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["lesson_exercise_id"], ["lesson_exercises.id"]),
        sa.ForeignKeyConstraint(["vocabulary_item_id"], ["vocabulary_items.id"]),
        sa.PrimaryKeyConstraint("lesson_exercise_id", "vocabulary_item_id"),
    )
    op.create_index(
        op.f("ix_lesson_exercise_vocabulary_vocabulary_item_id"),
        "lesson_exercise_vocabulary",
        ["vocabulary_item_id"],
    )

    op.create_table(
        "user_progress",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mastery_level", sa.Float(), nullable=False),
        sa.Column("last_practiced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("times_correct", sa.Integer(), nullable=False),
        sa.Column("times_attempted", sa.Integer(), nullable=False),
        sa.Column("streak_count", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "skill_id", name="uq_user_progress_skill"),
    )
    op.create_index(op.f("ix_user_progress_user_id"), "user_progress", ["user_id"])
    op.create_index(op.f("ix_user_progress_skill_id"), "user_progress", ["skill_id"])

    op.create_table(
        "user_exercise_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("exercise_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("submitted_answer", postgresql.JSONB(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=True),
        sa.Column("llm_feedback", sa.Text(), nullable=True),
        sa.Column(
            "attempted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["exercise_id"], ["lesson_exercises.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_user_exercise_attempts_user_id"), "user_exercise_attempts", ["user_id"]
    )
    op.create_index(
        op.f("ix_user_exercise_attempts_exercise_id"), "user_exercise_attempts", ["exercise_id"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("user_exercise_attempts")
    op.drop_table("user_progress")
    op.drop_table("lesson_exercise_vocabulary")
    op.drop_table("lesson_exercises")
    op.drop_table("review_logs")
    op.drop_table("cards")
    op.drop_table("vocabulary_items")
    op.drop_table("user_courses")
    op.drop_table("skills")
    op.drop_table("decks")
    op.drop_table("courses")
    op.drop_table("users")
    op.drop_table("languages")
