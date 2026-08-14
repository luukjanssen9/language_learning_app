"""Generates example sentences for a vocabulary word via an `LLMProvider`.
Pure function, no DB access -- same convention as `conjugation.py`/
`exercise_grading.py`; the caller (route) is responsible for loading the
vocabulary item's course/language rows and for persisting the result as
`VocabularyExample` rows.

The prompt is built entirely from arguments -- target/base language name,
the word itself, its part of speech -- never a hardcoded language name,
per this project's language-agnostic-by-design principle.
"""

from pydantic import BaseModel

from app.services.llm.base import LLMProvider


class ExampleSentence(BaseModel):
    target_text: str
    base_text: str


class ExampleSentenceList(BaseModel):
    examples: list[ExampleSentence]


async def generate_example_sentences(
    llm: LLMProvider,
    target_language_name: str,
    base_language_name: str,
    target_text: str,
    part_of_speech: str | None,
    count: int = 3,
) -> list[ExampleSentence]:
    pos_clause = f" ({part_of_speech})" if part_of_speech else ""
    prompt = (
        f"Write {count} short, natural example sentences in {target_language_name} "
        f'that each use the word "{target_text}"{pos_clause}. '
        f"For each sentence, also give its {base_language_name} translation. "
        "Keep the sentences simple, everyday, and appropriate for a beginner "
        "language learner."
    )
    result = await llm.generate_structured(prompt, ExampleSentenceList, model_tier="fast")
    return result.examples
