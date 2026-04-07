import os

import pytest

from tests.fixtures.build_fixtures import build_all_fixtures

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/whoop_lens",
)


@pytest.fixture(scope="session", autouse=True)
def _build_fixtures() -> None:
    build_all_fixtures()
