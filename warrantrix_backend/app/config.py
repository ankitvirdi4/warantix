from functools import lru_cache
from typing import Literal

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    app_name: str = Field("Warranty Intelligence Copilot", env="APP_NAME")
    env: Literal["dev", "prod"] = Field("dev", env="ENV")
    database_url: str = Field(
        "postgresql+psycopg2://postgres:postgres@db:5432/warrantrix", env="DATABASE_URL"
    )
    jwt_secret_key: str = Field("supersecret", env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
