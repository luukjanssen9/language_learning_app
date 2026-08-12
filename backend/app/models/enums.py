import enum

from sqlalchemy import Enum


def pg_enum(enum_cls: type[enum.Enum], **kwargs) -> Enum:
    """`Enum` column factory that stores the member's `.value` (e.g.
    "target_to_base") instead of SQLAlchemy's default of `.name` (e.g.
    "TARGET_TO_BASE"), and stores it as plain VARCHAR (`native_enum=False`)
    rather than a Postgres native enum type — adding a new member later is
    then a plain migration, not an `ALTER TYPE ... ADD VALUE`.
    """
    return Enum(
        enum_cls,
        native_enum=False,
        values_callable=lambda cls: [member.value for member in cls],
        **kwargs,
    )


class ScriptDirection(enum.StrEnum):
    LTR = "ltr"
    RTL = "rtl"


class CardDirection(enum.StrEnum):
    TARGET_TO_BASE = "target_to_base"
    BASE_TO_TARGET = "base_to_target"
    MIXED = "mixed"


class CardState(enum.StrEnum):
    NEW = "new"
    LEARNING = "learning"
    REVIEW = "review"
    RELEARNING = "relearning"


class ReviewRating(enum.StrEnum):
    AGAIN = "again"
    HARD = "hard"
    GOOD = "good"
    EASY = "easy"


class ExerciseType(enum.StrEnum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRANSLATION = "translation"
    FILL_IN_BLANK = "fill_in_blank"
    FREE_TEXT = "free_text"
