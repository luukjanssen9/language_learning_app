"""SQLAlchemy models. Import all modules here so Alembic autogenerate and
Base.metadata see every table.
"""

from app.models.base import Base
from app.models.card import Card
from app.models.course import Course
from app.models.deck import Deck
from app.models.language import Language
from app.models.lesson_exercise import LessonExercise, LessonExerciseVocabulary
from app.models.review_log import ReviewLog
from app.models.skill import Skill
from app.models.user import User
from app.models.user_course import UserCourse
from app.models.user_exercise_attempt import UserExerciseAttempt
from app.models.user_progress import UserProgress
from app.models.vocabulary import VocabularyItem
from app.models.vocabulary_audio import VocabularyAudio
from app.models.vocabulary_example import VocabularyExample

__all__ = [
    "Base",
    "Card",
    "Course",
    "Deck",
    "Language",
    "LessonExercise",
    "LessonExerciseVocabulary",
    "ReviewLog",
    "Skill",
    "User",
    "UserCourse",
    "UserExerciseAttempt",
    "UserProgress",
    "VocabularyAudio",
    "VocabularyExample",
    "VocabularyItem",
]
