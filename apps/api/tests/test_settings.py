import pytest
from pydantic import ValidationError

from app.settings import Settings


def test_settings_loads_with_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://localhost/test")
    s = Settings()
    assert s.max_upload_mb == 50
    assert s.share_ttl_days == 30
    assert s.log_level == "INFO"
    assert s.cors_origin == ["http://localhost:3000"]


def test_settings_parses_csv_cors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://localhost/test")
    monkeypatch.setenv("CORS_ORIGIN", "https://a.com,https://b.com")
    s = Settings()
    assert s.cors_origin == ["https://a.com", "https://b.com"]


def test_settings_requires_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValidationError):
        Settings()
