"""Ranks what a user is currently struggling with, from three existing
signals -- see PLAN.md's "adaptive weak-point targeting" decision for why
these three and not a new unified score. Like `known_vocabulary_lookup.py`,
this touches the DB directly (plain aggregate SELECTs) -- there's no
meaningful "pure" version of "what is this user currently bad at."
"""

import uuid

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.card import Card
from app.models.deck import Deck
from app.models.lesson_exercise import LessonExercise, LessonExerciseVocabulary
from app.models.skill import Skill
from app.models.user_exercise_attempt import UserExerciseAttempt
from app.models.user_progress import UserProgress
from app.models.vocabulary import VocabularyItem

# Below these, a single wrong answer would look like a "weak point" --
# require a little real signal first.
MIN_ATTEMPTS = 2
MAX_ACCURACY = 0.7
MAX_MASTERY = 0.7
DEFAULT_LIMIT = 5


async def get_weak_cards(
    db: AsyncSession, user_id: uuid.UUID, course_id: uuid.UUID, limit: int = DEFAULT_LIMIT
) -> list[dict]:
    """Flashcards with at least one real FSRS lapse, worst first. Cards with
    no `vocabulary_item_id` (rare manual override-only cards) are excluded --
    nothing meaningful to display as "the word."
    """
    result = await db.execute(
        select(
            VocabularyItem.id.label("vocabulary_item_id"),
            VocabularyItem.target_text,
            VocabularyItem.base_text,
            Deck.id.label("deck_id"),
            Deck.name.label("deck_name"),
            Card.lapses,
        )
        .select_from(Card)
        .join(VocabularyItem, Card.vocabulary_item_id == VocabularyItem.id)
        .join(Deck, Card.deck_id == Deck.id)
        .where(Deck.user_id == user_id, Deck.course_id == course_id, Card.lapses >= 1)
        .order_by(Card.lapses.desc(), Card.difficulty.desc().nullslast())
        .limit(limit)
    )
    return [dict(row._mapping) for row in result]


async def get_weak_lesson_words(
    db: AsyncSession, user_id: uuid.UUID, course_id: uuid.UUID, limit: int = DEFAULT_LIMIT
) -> list[dict]:
    """Words drilled inaccurately in lesson exercises, worst accuracy first.
    Grouped by (word, skill) rather than word alone -- a word drilled across
    multiple skills gets one row per skill, which is more precise, not less.
    Only graded attempts count (`is_correct IS NOT NULL`); free-text
    attempts awaiting grading don't exist in practice (grading is
    synchronous), but this guards the aggregate regardless.
    """
    accuracy = func.avg(case((UserExerciseAttempt.is_correct.is_(True), 1.0), else_=0.0))
    attempts = func.count(UserExerciseAttempt.id)
    result = await db.execute(
        select(
            VocabularyItem.id.label("vocabulary_item_id"),
            VocabularyItem.target_text,
            VocabularyItem.base_text,
            Skill.id.label("skill_id"),
            Skill.name.label("skill_name"),
            accuracy.label("accuracy"),
            attempts.label("times_attempted"),
        )
        .select_from(UserExerciseAttempt)
        .join(LessonExercise, UserExerciseAttempt.exercise_id == LessonExercise.id)
        .join(
            LessonExerciseVocabulary,
            LessonExerciseVocabulary.lesson_exercise_id == LessonExercise.id,
        )
        .join(VocabularyItem, LessonExerciseVocabulary.vocabulary_item_id == VocabularyItem.id)
        .join(Skill, LessonExercise.skill_id == Skill.id)
        .where(
            UserExerciseAttempt.user_id == user_id,
            VocabularyItem.course_id == course_id,
            UserExerciseAttempt.is_correct.is_not(None),
        )
        .group_by(VocabularyItem.id, Skill.id)
        .having(attempts >= MIN_ATTEMPTS, accuracy < MAX_ACCURACY)
        .order_by(accuracy.asc())
        .limit(limit)
    )
    return [dict(row._mapping) for row in result]


async def get_weak_skills(
    db: AsyncSession, user_id: uuid.UUID, course_id: uuid.UUID, limit: int = DEFAULT_LIMIT
) -> list[dict]:
    """Skills with low overall mastery, worst first. `mastery_level` is
    already exactly this signal -- maintained incrementally by
    `submit_lesson_exercise_attempt` (app/api/routes/lesson_exercises.py) --
    no new computation needed here.
    """
    result = await db.execute(
        select(
            Skill.id.label("skill_id"),
            Skill.name.label("skill_name"),
            UserProgress.mastery_level,
            UserProgress.times_attempted,
        )
        .select_from(UserProgress)
        .join(Skill, UserProgress.skill_id == Skill.id)
        .where(
            UserProgress.user_id == user_id,
            Skill.course_id == course_id,
            UserProgress.times_attempted >= MIN_ATTEMPTS,
            UserProgress.mastery_level < MAX_MASTERY,
        )
        .order_by(UserProgress.mastery_level.asc())
        .limit(limit)
    )
    return [dict(row._mapping) for row in result]
