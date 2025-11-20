"""Application configuration using Pydantic settings."""
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Runtime configuration for the Tweet Capture service."""

    app_env: str = Field("development", alias="APP_ENV")
    app_version: str = Field("1.0.0", alias="APP_VERSION")

    gcp_project_id: str = Field(..., alias="GCP_PROJECT_ID")
    firestore_database: str = Field("(default)", alias="FIRESTORE_DATABASE")
    pubsub_topic: str = Field(..., alias="PUBSUB_TOPIC")

    jwt_secret_key: str = Field(..., alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM")
    access_token_expire_seconds: int = Field(3600, alias="ACCESS_TOKEN_EXPIRE_SECONDS")
    refresh_token_expire_days: int = Field(30, alias="REFRESH_TOKEN_EXPIRE_DAYS")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()


settings = get_settings()
