"""
Application Configuration Module.

Loads environment variables using Pydantic Settings with
strong typing and default fallbacks.
"""

from typing import List, Optional, Union

# pyrefly: ignore [missing-import]
from pydantic import field_validator
# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global application settings and environment configurations."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    PROJECT_NAME: str = "CareArc Backend API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database connection parameters
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres_password"
    POSTGRES_DB: str = "carearc_db"

    DATABASE_URL: Optional[str] = None

    # CORS configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(
        cls,
        v: Union[str, List[str]],
    ) -> List[str]:
        """Parse CORS origins from a comma-separated string or list."""

        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]

        if isinstance(v, list):
            return v

        return [
            "http://localhost:5173",
            "http://localhost:3000",
        ]

    @property
    def async_database_url(self) -> str:
        """
        Construct or return the asynchronous SQLAlchemy
        database connection URL.
        """

        if self.DATABASE_URL:

            # Convert a standard PostgreSQL URL to SQLAlchemy asyncpg.
            if self.DATABASE_URL.startswith("postgresql://"):
                return self.DATABASE_URL.replace(
                    "postgresql://",
                    "postgresql+asyncpg://",
                    1,
                )

            # Support SQLite async testing if needed later.
            if self.DATABASE_URL.startswith("sqlite://"):
                return self.DATABASE_URL.replace(
                    "sqlite://",
                    "sqlite+aiosqlite://",
                    1,
                )

            return self.DATABASE_URL

        return (
            f"postgresql+asyncpg://"
            f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}"
            f"/{self.POSTGRES_DB}"
        )


# Global settings instance
settings = Settings()