"""Grades a FREE_TEXT LessonExercise answer via an `LLMProvider`. Pure
function, no DB access -- same convention as `sentence_generation.py`;
the caller (route) is responsible for loading the exercise/language rows
and persisting the result onto `UserExerciseAttempt`.

A FREE_TEXT exercise's `prompt` is one of two shapes, distinguished by
which key is present:
- `source_text`: translate a full sentence, any natural phrasing accepted
  (unlike TRANSLATION's exact-match against one canonical string).
- `question_text`: answer a question in the target language -- tests
  production, not just translation.
"""

from pydantic import BaseModel

from app.services.llm.base import LLMProvider


class FreeTextGradeResult(BaseModel):
    is_correct: bool
    feedback: str


def _build_instruction(
    target_language_name: str, base_language_name: str, prompt: dict
) -> str:
    if "source_text" in prompt:
        return (
            f'The student was asked to translate this {base_language_name} '
            f'sentence into {target_language_name}: "{prompt["source_text"]}"'
        )
    return (
        f"The student was asked to answer this {target_language_name} "
        f'question, in {target_language_name}: "{prompt["question_text"]}"'
    )


async def grade_free_text_attempt(
    llm: LLMProvider,
    target_language_name: str,
    base_language_name: str,
    prompt: dict,
    submitted_text: str,
) -> FreeTextGradeResult:
    instruction = _build_instruction(target_language_name, base_language_name, prompt)
    grading_prompt = (
        f"{instruction}\n"
        f'Their answer: "{submitted_text}"\n\n'
        "Judge whether this is a correct, natural response for a beginner "
        f"{target_language_name} learner. Minor spelling or accent slips are "
        "fine as long as the meaning is clearly right. Give brief, "
        "encouraging feedback (1-2 sentences) explaining why -- if it's "
        "wrong, say what a correct answer would look like."
    )
    return await llm.generate_structured(
        grading_prompt, FreeTextGradeResult, model_tier="reasoning"
    )
