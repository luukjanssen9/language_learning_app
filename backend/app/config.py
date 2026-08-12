from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App configuration, read from environment variables / .env.

    Looks for `.env` one directory up first (the repo-root `.env` that
    docker-compose and `.env.example` describe), then a local `backend/.env`
    override if present.
    """

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Database ---
    database_url: str = "postgresql+asyncpg://language_app:language_app@localhost:5432/language_app"

    # --- LLM provider ---
    llm_provider: str = "gemini"
    gemini_api_key: str = ""
    gemini_fast_model: str = "gemini-3.1-flash-lite"
    gemini_reasoning_model: str = "gemini-3.5-flash"
    anthropic_api_key: str = ""

    # --- App ---
    environment: str = "development"
    secret_key: str = "dev-secret-change-me"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
