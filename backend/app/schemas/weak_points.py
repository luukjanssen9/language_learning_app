import uuid

from pydantic import BaseModel


class WeakCardResult(BaseModel):
    """A flashcard the user keeps failing -- see `get_weak_cards`
    (app/services/weak_points.py).
    """

    vocabulary_item_id: uuid.UUID
    target_text: str
    base_text: str
    deck_id: uuid.UUID
    deck_name: str
    lapses: int


class WeakLessonWordResult(BaseModel):
    """A word the user is inaccurate on within a specific skill's lesson
    exercises -- see `get_weak_lesson_words` (app/services/weak_points.py).
    """

    vocabulary_item_id: uuid.UUID
    target_text: str
    base_text: str
    skill_id: uuid.UUID
    skill_name: str
    accuracy: float
    times_attempted: int


class WeakSkillResult(BaseModel):
    """A skill with low overall mastery -- see `get_weak_skills`
    (app/services/weak_points.py).
    """

    skill_id: uuid.UUID
    skill_name: str
    mastery_level: float
    times_attempted: int


class WeakPointsResponse(BaseModel):
    weak_cards: list[WeakCardResult]
    weak_lesson_words: list[WeakLessonWordResult]
    weak_skills: list[WeakSkillResult]
