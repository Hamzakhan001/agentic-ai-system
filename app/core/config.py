from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    app_env: str = "development"
    log_level: str = "INFO"
    api_prefix: str = "/api/v1"
    retrieval_top_k: int = 4
    max_document_chars: int = 12000


@lru_cache
def get_settings() -> Settings:
    return Settings()
