"""Grades a submitted `LessonExercise` answer against its `prompt` JSON,
branching by `exercise_type`. Pure function except that `CONJUGATION`
also calls the conjugation service against the target language's
`grammar_config` (passed in, not fetched here -- no DB access in this
module, same convention as fsrs_engine.py/conjugation.py).
"""

import unicodedata

from app.models.enums import ExerciseType
from app.models.lesson_exercise import LessonExercise
from app.services.conjugation import ConjugationError, conjugate


def _strip_accents(text: str) -> str:
    # NFKD decomposes an accented character into base + combining mark
    # (e.g. "á" -> "a" + U+0301); dropping the marks (Unicode category
    # "Mn") leaves the unaccented base letters.
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def _normalize(text: str) -> str:
    # Accent-insensitive by request (2026-08-14): typing Spanish accents
    # on a US keyboard is real friction, and this is a scoped fix for
    # that specifically -- not general typo tolerance, which stays out
    # of scope for Phase 5's LLM grading.
    return _strip_accents(text.strip().lower())


def get_correct_answer(exercise: LessonExercise, grammar_config: dict | None) -> str | None:
    """The correct answer as a display string, for the typed-answer
    exercise types -- used both to grade (compared against the
    normalized submission) and to reveal to the learner after a wrong
    attempt (see PLAN.md's 2026-08-14 decision, conjugation practice
    only for now). Returns None for MULTIPLE_CHOICE (graded by index,
    no single "correct answer" string) and FREE_TEXT (not graded here).
    """
    prompt = exercise.prompt
    if exercise.exercise_type in (ExerciseType.TRANSLATION, ExerciseType.FILL_IN_BLANK):
        return prompt["correct_answer"]
    if exercise.exercise_type == ExerciseType.CONJUGATION:
        try:
            return conjugate(
                grammar_config or {},
                prompt["infinitive"],
                prompt["tense"],
                prompt["mood"],
                prompt["pronoun"],
            )
        except ConjugationError:
            return None
    return None


def grade_attempt(
    exercise: LessonExercise, submitted_answer: dict, grammar_config: dict | None
) -> bool | None:
    """Returns True/False for gradable types, None for FREE_TEXT --
    matches `UserExerciseAttempt.is_correct`'s nullability. Free-text
    grading is Phase 5's LLM territory, not implemented here.
    """
    if exercise.exercise_type == ExerciseType.MULTIPLE_CHOICE:
        return submitted_answer.get("selected_index") == exercise.prompt["correct_index"]

    if exercise.exercise_type == ExerciseType.FREE_TEXT:
        return None

    correct_answer = get_correct_answer(exercise, grammar_config)
    if correct_answer is None:
        return False  # CONJUGATION with no resolvable rule for this combo

    submitted_key = "answer" if exercise.exercise_type == ExerciseType.CONJUGATION else "text"
    submitted = submitted_answer.get(submitted_key, "")
    return _normalize(submitted) == _normalize(correct_answer)
