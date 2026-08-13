"""Pure unit tests for exercise grading -- no DB, no HTTP client.
`LessonExercise` instances are constructed directly in memory (never
flushed to a session), same convention as test_fsrs_engine.py's `Card`
construction and test_conjugation_service.py's synthetic fixtures.
"""

import uuid

from app.models.enums import ExerciseType
from app.models.lesson_exercise import LessonExercise
from app.services.exercise_grading import get_correct_answer, grade_attempt


def _exercise(exercise_type: ExerciseType, prompt: dict) -> LessonExercise:
    return LessonExercise(skill_id=uuid.uuid4(), exercise_type=exercise_type, prompt=prompt)


def test_multiple_choice_grades_by_index():
    exercise = _exercise(
        ExerciseType.MULTIPLE_CHOICE,
        {"question": "Q", "options": ["a", "b"], "correct_index": 1},
    )
    assert grade_attempt(exercise, {"selected_index": 1}, None) is True
    assert grade_attempt(exercise, {"selected_index": 0}, None) is False


def test_translation_accent_insensitive():
    # Missing Spanish accents on a non-Spanish keyboard is real friction
    # (2026-08-14 decision) -- "adios" should grade the same as "adiós".
    exercise = _exercise(
        ExerciseType.TRANSLATION, {"source_text": "goodbye", "correct_answer": "adiós"}
    )
    assert grade_attempt(exercise, {"text": "adios"}, None) is True
    assert grade_attempt(exercise, {"text": "ADIÓS"}, None) is True
    assert grade_attempt(exercise, {"text": "  Adios  "}, None) is True


def test_translation_wrong_word_still_wrong():
    exercise = _exercise(
        ExerciseType.TRANSLATION, {"source_text": "goodbye", "correct_answer": "adiós"}
    )
    assert grade_attempt(exercise, {"text": "hola"}, None) is False


def test_fill_in_blank_accent_insensitive():
    exercise = _exercise(
        ExerciseType.FILL_IN_BLANK, {"sentence": "___ tarde.", "correct_answer": "más"}
    )
    assert grade_attempt(exercise, {"text": "mas"}, None) is True


def test_conjugation_accent_insensitive():
    # Fixture ending is deliberately accented ("ás") to exercise the
    # accent-stripping path -- not a real-Spanish claim, same convention
    # as test_conjugation_service.py's synthetic fixtures.
    config = {
        "conjugation": {
            "regular_endings": {"ar": {"present": {"indicative": {"tú": "ás"}}}},
            "irregular_verbs": {},
        },
    }
    exercise = _exercise(
        ExerciseType.CONJUGATION,
        {"infinitive": "hablar", "tense": "present", "mood": "indicative", "pronoun": "tú"},
    )
    assert grade_attempt(exercise, {"answer": "hablas"}, config) is True
    assert grade_attempt(exercise, {"answer": "hablás"}, config) is True


def test_conjugation_unresolvable_grades_false_not_error():
    exercise = _exercise(
        ExerciseType.CONJUGATION,
        {"infinitive": "vivir", "tense": "present", "mood": "indicative", "pronoun": "yo"},
    )
    assert grade_attempt(exercise, {"answer": "vivo"}, {"conjugation": {}}) is False


def test_free_text_not_graded():
    exercise = _exercise(ExerciseType.FREE_TEXT, {})
    assert grade_attempt(exercise, {"text": "anything"}, None) is None


def test_get_correct_answer_multiple_choice_returns_none():
    exercise = _exercise(
        ExerciseType.MULTIPLE_CHOICE,
        {"question": "Q", "options": ["a", "b"], "correct_index": 1},
    )
    assert get_correct_answer(exercise, None) is None


def test_get_correct_answer_translation():
    exercise = _exercise(
        ExerciseType.TRANSLATION, {"source_text": "goodbye", "correct_answer": "adiós"}
    )
    assert get_correct_answer(exercise, None) == "adiós"


def test_get_correct_answer_conjugation():
    config = {
        "conjugation": {
            "regular_endings": {"ar": {"present": {"indicative": {"tú": "as"}}}},
            "irregular_verbs": {},
        },
    }
    exercise = _exercise(
        ExerciseType.CONJUGATION,
        {"infinitive": "hablar", "tense": "present", "mood": "indicative", "pronoun": "tú"},
    )
    assert get_correct_answer(exercise, config) == "hablas"


def test_get_correct_answer_unresolvable_conjugation_returns_none():
    exercise = _exercise(
        ExerciseType.CONJUGATION,
        {"infinitive": "vivir", "tense": "present", "mood": "indicative", "pronoun": "yo"},
    )
    assert get_correct_answer(exercise, {"conjugation": {}}) is None


def test_get_correct_answer_free_text_returns_none():
    exercise = _exercise(ExerciseType.FREE_TEXT, {})
    assert get_correct_answer(exercise, None) is None
