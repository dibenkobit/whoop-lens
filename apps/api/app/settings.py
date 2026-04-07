from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = Field(..., alias="DATABASE_URL")
    # str | list[str] prevents pydantic-settings from attempting JSON decode on
    # the raw env value; the field_validator then normalises to list[str].
    cors_origin: str | list[str] = Field(
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


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
