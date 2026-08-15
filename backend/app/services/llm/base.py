"""Provider-agnostic LLM interface. Every Phase 5 feature (example
generation, free-text grading, mnemonics, auto-card-gen) calls an
`LLMProvider` through `generate_structured` and gets back a parsed
Pydantic model -- never raw text to hand-parse, per this project's own
"never parse free text" convention for anything the app consumes
programmatically.

Swapping providers (e.g. Gemini -> Anthropic) means adding a new
`LLMProvider` implementation and pointing `LLM_PROVIDER` at it (see
`app/services/llm/__init__.py`) -- never a call-site change, since every
call site only ever depends on this Protocol.
"""

from typing import Literal, Protocol, TypeVar

from pydantic import BaseModel

BaseModelT = TypeVar("BaseModelT", bound=BaseModel)

ModelTier = Literal["fast", "reasoning"]


class ChatTurn(BaseModel):
    """One turn in a multi-turn conversation, oldest-first when passed as
    a list -- see `LLMProvider.generate_chat_reply`.
    """

    role: Literal["user", "assistant"]
    text: str


class LLMError(Exception):
    """Raised on provider/network failure, or a response that doesn't
    parse against the requested `response_model`. Callers (routes) are
    expected to let this propagate -- `app/main.py` maps it to a 502,
    the same way `IntegrityError` is mapped globally to a 409.
    """


class LLMProvider(Protocol):
    async def generate_structured(
        self,
        prompt: str,
        response_model: type[BaseModelT],
        model_tier: ModelTier = "fast",
    ) -> BaseModelT:
        """Sends `prompt`, asking the model to return JSON matching
        `response_model`'s schema, and returns a parsed instance of it.

        `model_tier` picks between a cheap/fast model for high-volume,
        low-complexity calls and a stronger model for calls that need
        more reasoning (mirrors this project's Haiku/Sonnet-style split
        -- see PLAN.md's 2026-08-11 LLM-provider decision).
        """
        ...

    async def generate_chat_reply(
        self,
        system_prompt: str,
        history: list[ChatTurn],
        response_model: type[BaseModelT],
        model_tier: ModelTier = "fast",
    ) -> BaseModelT:
        """Same structured-JSON contract as `generate_structured`, but for
        multi-turn conversations: `system_prompt` sets persona/instructions
        (sent once, out-of-band from the turns, the same role a single
        one-shot `prompt` plays elsewhere), `history` is the full
        conversation so far so the model has real conversational memory,
        not just the latest message -- see PLAN.md's Phase 6 decision for
        why `generate_structured` alone (single prompt string, no message
        list) wasn't enough for a chat feature.
        """
        ...
