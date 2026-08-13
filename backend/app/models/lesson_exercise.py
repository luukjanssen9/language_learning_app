import uuid

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, UUIDPkMixin
from app.models.enums import ExerciseType, pg_enum


class LessonExercise(UUIDPkMixin, CreatedAtMixin, Base):
    """A single exercise within a Skill. `prompt` shape varies by
    `exercise_type` (JSONB rather than one column set per type).
    """

    __tablename__ = "lesson_exercises"

    skill_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("skills.id"), nullable=False, index=True
    )
    exercise_type: Mapped[ExerciseType] = mapped_column(
        pg_enum(ExerciseType, length=20), nullable=False
    )
    prompt: Mapped[dict] = mapped_column(JSONB, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Same specialty-module tag as Skill.specialty_module, set redundantly
    # here too so exercise-level queries (e.g. "every CONJUGATION attempt
    # across any skill" for Phase 5 analytics) don't need a join.
    specialty_module: Mapped[str | None] = mapped_column(String(50), nullable=True)

    def __repr__(self) -> str:
        return f"<LessonExercise {self.id} type={self.exercise_type}>"


class LessonExerciseVocabulary(Base):
    """Many-to-many: which VocabularyItems a given exercise drills. Feeds
    adaptive weak-point targeting (Phase 5).
    """

    __tablename__ = "lesson_exercise_vocabulary"

    lesson_exercise_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("lesson_exercises.id"), primary_key=True
    )
    vocabulary_item_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("vocabulary_items.id"), primary_key=True, index=True
    )
