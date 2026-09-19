"""Validated application settings and configuration values."""

from enum import StrEnum

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class StorageBackend(StrEnum):
    """Persistence implementations supported by the application."""

    DATABASE = "database"
    MEMORY = "memory"


class Settings(BaseSettings):
    """Typed application settings loaded from environment variables and .env."""

    database_url: str | None = None
    database_echo_sql: bool = False
    storage_backend: StorageBackend = StorageBackend.DATABASE

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def require_database_url_for_database_backend(self) -> "Settings":
        """Require database credentials only when PostgreSQL is selected."""

        if self.storage_backend is StorageBackend.DATABASE and not self.database_url:
            raise ValueError(
                "DATABASE_URL is required when STORAGE_BACKEND=database"
            )
        return self
