from functools import lru_cache
from typing import Annotated, Literal, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field("Warranty Intelligence Copilot", env="APP_NAME")
    env: Literal["dev", "prod"] = Field("dev", env="ENV")
    database_url: str = Field(
        "postgresql+psycopg2://postgres:postgres@db:5432/warrantrix", env="DATABASE_URL"
    )
    jwt_secret_key: str = Field("supersecret", env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    openai_embedding_model: str = Field("text-embedding-3-small", env="OPENAI_EMBEDDING_MODEL")
    openai_completion_model: str = Field("gpt-4o-mini", env="OPENAI_COMPLETION_MODEL")
    qdrant_url: str = Field("http://qdrant:6333", env="QDRANT_URL")
    qdrant_api_key: Optional[str] = Field(None, env="QDRANT_API_KEY")
    embedding_batch_size: int = Field(64, env="EMBEDDING_BATCH_SIZE")
    clustering_min_claims: int = Field(50, env="CLUSTERING_MIN_CLAIMS")
    num_clusters_default: int = Field(10, env="NUM_CLUSTERS_DEFAULT")
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "https://YOUR_FRONTEND_NAME.vercel.app",
        ],
        env="CORS_ORIGINS",
    )

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    @field_validator("cors_origins", mode="before")
    def split_cors_origins(cls, value: Optional[str]):
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
