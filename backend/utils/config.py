from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = "development"
    database_url: str = "sqlite:///./llm_eval.db"
    api_key: str = "local-dev-key"
    require_auth: bool = False

    llm_provider: str = "heuristic"
    llm_model: str = "grok-4.20-reasoning"
    xai_api_key: str = ""
    xai_base_url: str = "https://api.x.ai/v1"

    translation_provider: str = "heuristic"
    translation_model: str = "grok-4.20-reasoning"

    embedding_provider: str = "multilingual_vector"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 12
    vector_db: str = "pgvector"
    multilingual_embeddings: bool = True

    language_mode: str = "auto"
    default_output_language: str = "en"
    strict_language_match: bool = True
    allow_language_override: bool = True
    language_retry_limit: int = 2

    enable_feedback_loop: bool = True
    feedback_store: str = "postgres"
    confidence_threshold: float = 0.75

    knowledge_base_path: str = "backend/rag/knowledge_base"
    cors_origins: str = Field(default="*", alias="BACKEND_CORS_ORIGINS")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
