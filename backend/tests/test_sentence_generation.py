"""Pure unit tests for the sentence-generation service -- no DB, no HTTP
client, no real LLM call. Same convention as `test_conjugation_service.py`:
a minimal fake standing in for the real dependency (here, `LLMProvider`
instead of a `grammar_config` fixture dict).
"""

from pydantic import BaseModel

from app.services.llm.base import ModelTier
from app.services.sentence_generation import (
    ExampleSentence,
    ExampleSentenceList,
    generate_example_sentences,
)


class FakeLLMProvider:
    """Records the prompt/model it was called with and returns a canned
    response, regardless of `response_model` -- fine for these tests since
    every call site here always passes `ExampleSentenceList`.
    """

    def __init__(self, canned_response: BaseModel) -> None:
        self.canned_response = canned_response
        self.last_prompt: str | None = None
        self.last_model_tier: ModelTier | None = None
        self.call_count = 0

    async def generate_structured(
        self, prompt: str, response_model: type, model_tier: ModelTier = "fast"
    ) -> BaseModel:
        self.last_prompt = prompt
        self.last_model_tier = model_tier
        self.call_count += 1
        return self.canned_response


async def test_generate_example_sentences_returns_provider_examples():
    canned = ExampleSentenceList(
        examples=[
            ExampleSentence(target_text="Hola, ¿cómo estás?", base_text="Hi, how are you?"),
            ExampleSentence(target_text="Hola de nuevo.", base_text="Hello again."),
        ]
    )
    fake = FakeLLMProvider(canned)

    result = await generate_example_sentences(
        fake,
        target_language_name="Spanish",
        base_language_name="English",
        target_text="hola",
        part_of_speech="interjection",
        count=2,
    )

    assert result == canned.examples


async def test_generate_example_sentences_prompt_uses_passed_in_language_names():
    # Proves the prompt is templated from the arguments, not a hardcoded
    # language -- Dutch/English here specifically because this project's
    # default/first-built language was Spanish, so a test that only ever
    # used Spanish wouldn't catch a hardcoded "Spanish" slipping in.
    fake = FakeLLMProvider(ExampleSentenceList(examples=[]))

    await generate_example_sentences(
        fake,
        target_language_name="Dutch",
        base_language_name="English",
        target_text="hallo",
        part_of_speech=None,
        count=3,
    )

    assert fake.last_prompt is not None
    assert "Dutch" in fake.last_prompt
    assert "English" in fake.last_prompt
    assert "hallo" in fake.last_prompt
    assert "Spanish" not in fake.last_prompt


async def test_generate_example_sentences_omits_part_of_speech_when_absent():
    fake = FakeLLMProvider(ExampleSentenceList(examples=[]))

    await generate_example_sentences(
        fake,
        target_language_name="Spanish",
        base_language_name="English",
        target_text="hola",
        part_of_speech=None,
        count=3,
    )

    assert fake.last_prompt is not None
    assert "(" not in fake.last_prompt


async def test_generate_example_sentences_uses_fast_model_tier():
    fake = FakeLLMProvider(ExampleSentenceList(examples=[]))

    await generate_example_sentences(
        fake,
        target_language_name="Spanish",
        base_language_name="English",
        target_text="hola",
        part_of_speech=None,
    )

    assert fake.last_model_tier == "fast"
