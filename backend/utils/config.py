from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = "development"
    database_url: str = "sqlite:///./llm_eval.db"
    default_contract_path: str = "contracts/default.yaml"
    api_key: str = "local-dev-key"
    require_auth: bool = False
    llm_provider: str = "heuristic"
    llm_model: str = "gpt-4o-mini"
    openai_api_key: str = ""
    embedding_provider: str = "lexical"
    embedding_model: str = "text-embedding-3-small"
    knowledge_base_path: str = "backend/rag/knowledge_base"
    cors_origins: str = "*"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
