"""`LLMProvider` implementation backed by Google's Gemini API, via the
`google-genai` SDK. The only module that imports `google.genai` directly
-- same "one module owns the third-party library" convention as
`app/services/fsrs_engine.py` for the `fsrs` package.
"""

from google import genai
from google.genai import types

from app.config import settings

from .base import BaseModelT, ChatTurn, LLMError, ModelTier


class GeminiProvider:
    def __init__(self, api_key: str, fast_model: str, reasoning_model: str) -> None:
        self._client = genai.Client(api_key=api_key)
        self._models = {"fast": fast_model, "reasoning": reasoning_model}

    async def generate_structured(
        self,
        prompt: str,
        response_model: type[BaseModelT],
        model_tier: ModelTier = "fast",
    ) -> BaseModelT:
        try:
            response = await self._client.aio.models.generate_content(
                model=self._models[model_tier],
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=response_model,
                ),
            )
        except Exception as exc:
            raise LLMError(f"Gemini request failed: {exc}") from exc

        if response.parsed is None:
            raise LLMError("Gemini response did not match the requested schema")
        return response.parsed

    async def generate_chat_reply(
        self,
        system_prompt: str,
        history: list[ChatTurn],
        response_model: type[BaseModelT],
        model_tier: ModelTier = "fast",
    ) -> BaseModelT:
        contents = [
            types.Content(
                role="model" if turn.role == "assistant" else "user",
                parts=[types.Part(text=turn.text)],
            )
            for turn in history
        ]
        try:
            response = await self._client.aio.models.generate_content(
                model=self._models[model_tier],
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    response_schema=response_model,
                ),
            )
        except Exception as exc:
            raise LLMError(f"Gemini request failed: {exc}") from exc

        if response.parsed is None:
            raise LLMError("Gemini response did not match the requested schema")
        return response.parsed


def build_gemini_provider() -> GeminiProvider:
    return GeminiProvider(
        api_key=settings.gemini_api_key,
        fast_model=settings.gemini_fast_model,
        reasoning_model=settings.gemini_reasoning_model,
    )
