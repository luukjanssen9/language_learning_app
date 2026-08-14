"""Generates a short reading passage plus comprehension questions via an
`LLMProvider`, built from a list of words the learner already knows (i+1:
mostly known words, a handful of genuinely new ones). Pure function, no DB
access -- same convention as `journal_correction.py`; the caller (route) is
responsible for loading `known_words` (see `known_vocabulary_lookup.py`)
and persisting the result as a `ReadingPassage`.
"""

from pydantic import BaseModel

from app.services.llm.base import LLMProvider

DEFAULT_NEW_WORD_COUNT = 5


class NewVocabularyWordResult(BaseModel):
    target_text: str
    base_text: str


class QuestionResult(BaseModel):
    question_text: str
    reference_answer: str


class ReadingPassageResult(BaseModel):
    target_text: str
    base_text: str
    new_vocabulary: list[NewVocabularyWordResult]
    questions: list[QuestionResult]


async def generate_reading_passage(
    llm: LLMProvider,
    target_language_name: str,
    base_language_name: str,
    known_words: list[str],
    new_word_count: int = DEFAULT_NEW_WORD_COUNT,
) -> ReadingPassageResult:
    if known_words:
        vocab_clause = (
            f"The learner already knows these {target_language_name} words: "
            f"{', '.join(known_words)}. Write mostly using words from this list."
        )
    else:
        vocab_clause = (
            f"The learner is a complete beginner in {target_language_name} -- "
            "use only very basic, common vocabulary."
        )

    prompt = (
        f"{vocab_clause} You may also introduce up to {new_word_count} new, "
        f"slightly-more-advanced {target_language_name} words the learner "
        "hasn't seen yet, if they fit naturally.\n\n"
        f"Write a short, natural {target_language_name} reading passage "
        "(roughly 80-150 words) on any everyday topic. Return:\n"
        "- target_text: the passage itself.\n"
        f"- base_text: its full {base_language_name} translation.\n"
        "- new_vocabulary: every word or short phrase you used that is NOT "
        "in the learner's known-word list above, each as {target_text, "
        "base_text} -- omit this if you didn't introduce any.\n"
        "- questions: exactly 3 short-answer reading-comprehension questions "
        f"about the passage, written in {target_language_name}, each as "
        "{question_text, reference_answer} -- reference_answer is a model "
        "correct answer, not shown to the learner, used only for grading."
    )
    return await llm.generate_structured(prompt, ReadingPassageResult, model_tier="reasoning")
