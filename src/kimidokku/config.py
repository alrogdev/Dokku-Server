"""Application configuration management."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Base domain for auto-generated domains
    kimidokku_domain: str = Field(default="app.localhost")

    # Dokku host
    dokku_host: str = Field(default="localhost")

    # UI Basic Auth
    auth_user: str = Field(default="admin")
    auth_pass: str = Field(default="changeme")

    # Let's Encrypt email
    letsencrypt_email: str | None = Field(default=None)

    # Database
    db_path: Path = Field(default=Path("./kimidokku.db"))

    # Webhook secret fallback
    webhook_secret_default: str | None = Field(default=None)

    # Environment
    environment: str = Field(default="development")

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment.lower() == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
