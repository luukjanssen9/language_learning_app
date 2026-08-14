from fastapi import APIRouter

from app.api.routes import (
    cards,
    courses,
    decks,
    journal_entries,
    known_vocabulary,
    languages,
    lesson_exercises,
    reading_passages,
    review_logs,
    skills,
    user_courses,
    user_exercise_attempts,
    user_progress,
    users,
    vocabulary,
)

api_router = APIRouter()
api_router.include_router(languages.router)
api_router.include_router(courses.router)
api_router.include_router(users.router)
api_router.include_router(user_courses.router)
api_router.include_router(decks.router)
api_router.include_router(vocabulary.router)
api_router.include_router(cards.router)
api_router.include_router(journal_entries.router)
api_router.include_router(known_vocabulary.router)
api_router.include_router(reading_passages.router)
api_router.include_router(skills.router)
api_router.include_router(lesson_exercises.router)
api_router.include_router(review_logs.router)
api_router.include_router(user_progress.router)
api_router.include_router(user_exercise_attempts.router)
