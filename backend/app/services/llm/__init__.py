"""Picks and caches the configured `LLMProvider`, purely from
`settings.llm_provider` -- the one place that decides which concrete
provider backs the app, so swapping providers is an env-var change
(`LLM_PROVIDER`), never a call-site change. Exposed as a FastAPI
dependency (`Depends(get_llm_provider)`) for the same reason
`app/database.py`'s `get_db` is: routes depend on the Protocol, tests
override this dependency with a fake.

Only "gemini" is implemented so far (this project has no Anthropic key
yet -- see PLAN.md's Known Issues). Adding a real second provider later
means a new module here plus one more branch below, not touching any
caller.
"""

from functools import lru_cache

from app.config import settings

from .base import LLMProvider
from .gemini import build_gemini_provider

__all__ = ["LLMProvider", "get_llm_provider"]


@lru_cache
def get_llm_provider() -> LLMProvider:
    if settings.llm_provider == "gemini":
        return build_gemini_provider()
    raise ValueError(f"Unsupported LLM_PROVIDER: {settings.llm_provider!r}")
