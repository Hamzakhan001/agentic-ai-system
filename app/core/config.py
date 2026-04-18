from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True
    )

    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536


    pinecone_api_key: str = Field(default="", alias="PINECONE_API_KEY")
    pinecone_index_name: str = "agentic-legal"
    pinecone_region: str = Field(default="us-east-1", alias="PINECONE_ENVIRONMENT")

    app_env: str = "development"
    log_level: str = "INFO"
    api_prefix: str = "/api/v1"


    retrieval_top_k: int = 4
    chunk_size: int = 1000
    chunk_overlap: int = 150
    max_document_chars: int = 40000

    tavily_api_key: str = ""
    companies_house_api_key: str = ""
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/agentic_legal"
    phoenix_enabled: bool = Field(default=False, alias="PHOENIX_ENABLED")
    phoenix_collector_endpoint: str = Field(default="http://127.0.0.1:6006", alias="PHOENIX_COLLECTOR_ENDPOINT")
    phoenix_project_name: str = Field(default="agentic-legal-review", alias="PHOENIX_PROJECT_NAME")
    phoenix_api_key: str = Field(default="", alias="PHOENIX_API_KEY")



@lru_cache()
def get_settings() -> Settings:
    return Settings()
