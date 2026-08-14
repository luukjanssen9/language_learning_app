"""Grades a free-text answer to a reading-passage comprehension question via
an `LLMProvider`. Pure function, no DB access -- same convention as
`free_text_grading.py`, which this mirrors field-for-field; the caller
(route) is responsible for loading the passage/question and persisting the
result onto a `ReadingPassageAttempt`.
"""

from pydantic import BaseModel

from app.services.llm.base import LLMProvider


class ComprehensionGradeResult(BaseModel):
    is_correct: bool
    feedback: str


async def grade_comprehension_answer(
    llm: LLMProvider,
    passage_text: str,
    question_text: str,
    reference_answer: str,
    submitted_answer: str,
) -> ComprehensionGradeResult:
    prompt = (
        f'The learner read this passage:\n"{passage_text}"\n\n'
        f'They were asked: "{question_text}"\n'
        f'A model correct answer is: "{reference_answer}"\n'
        f'Their actual answer: "{submitted_answer}"\n\n'
        "Judge whether their answer correctly demonstrates they understood "
        "that part of the passage -- the wording doesn't need to match the "
        "model answer, just the meaning. Give brief, encouraging feedback "
        "(1-2 sentences) explaining why -- if it's wrong, point them back to "
        "the relevant part of the passage."
    )
    return await llm.generate_structured(
        prompt, ComprehensionGradeResult, model_tier="reasoning"
    )
