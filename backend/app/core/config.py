from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "Dine Finder API"
    app_env: str = "dev"
    api_v1_prefix: str = "/api/v1"

    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = ""
    mysql_db: str = "yelp_lab1"

    jwt_secret_key: str = "change-this-in-env"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    cors_origins: str = "http://127.0.0.1:5173,http://localhost:5173"
    uploads_dir_name: str = "uploads"
    startup_db_check_enabled: bool = True
    startup_db_check_strict: bool = False

    tavily_api_key: str = ""
    llm_provider: str = "openai"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-5-haiku-latest"
    embedding_provider: str = "openai"
    vector_db_dir_name: str = "vector_store"
    vector_collection_name: str = "restaurants"
    ai_retrieval_top_k: int = 8
    ai_llm_intent_extraction_enabled: bool = False

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        password = quote_plus(self.mysql_password)
        return (
            f"mysql+pymysql://{self.mysql_user}:{password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_db}?charset=utf8mb4"
        )

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def uploads_dir(self) -> Path:
        return BASE_DIR / self.uploads_dir_name

    @property
    def vector_db_dir(self) -> Path:
        return BASE_DIR / self.vector_db_dir_name


@lru_cache
def get_settings() -> Settings:
    return Settings()
