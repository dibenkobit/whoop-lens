import os

import pytest

from tests.fixtures.build_fixtures import build_all_fixtures

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/whoop_lens",
)


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--snapshot-update",
        action="store_true",
        default=False,
        help="Regenerate snapshot files instead of asserting against them.",
    )


@pytest.fixture(scope="session", autouse=True)
def _build_fixtures() -> None:
    build_all_fixtures()
