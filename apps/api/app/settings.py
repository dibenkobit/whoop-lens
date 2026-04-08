from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = Field(..., alias="DATABASE_URL")
    cors_origin: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:3000"],
        alias="CORS_ORIGIN",
    )
    max_upload_mb: int = Field(default=50, alias="MAX_UPLOAD_MB")
    share_ttl_days: int = Field(default=30, alias="SHARE_TTL_DAYS")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @field_validator("cors_origin", mode="before")
    @classmethod
    def split_cors(cls, v: object) -> object:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @field_validator("database_url", mode="after")
    @classmethod
    def ensure_async_driver(cls, v: str) -> str:
        # Normalize any Postgres URL to use the asyncpg driver. Railway's
        # managed Postgres exposes DATABASE_URL as `postgresql://...`, but
        # both the app engine and Alembic env use SQLAlchemy's async API,
        # which requires an explicit async driver.
        if v.startswith("postgres://"):
            v = "postgresql://" + v[len("postgres://") :]
        if v.startswith("postgresql://") and "+asyncpg" not in v:
            v = "postgresql+asyncpg://" + v[len("postgresql://") :]
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
