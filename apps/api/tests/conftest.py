import os
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/whoop_lens",
)

from app.db.base import Base  # noqa: E402  (must come after env default)
from tests.fixtures.build_fixtures import build_all_fixtures  # noqa: E402

_DATABASE_URL = os.environ["DATABASE_URL"]


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


@pytest_asyncio.fixture(scope="session")
async def _test_engine() -> AsyncIterator[AsyncEngine]:
    """Session-scoped engine with NullPool — created inside the test event loop."""
    engine = create_async_engine(_DATABASE_URL, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(loop_scope="session")
async def db_session(_test_engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    """Per-test session that rolls back at the end."""
    connection: AsyncConnection = await _test_engine.connect()
    trans = await connection.begin()
    factory = async_sessionmaker(bind=connection, expire_on_commit=False, class_=AsyncSession)
    async with factory() as session:
        yield session
    await trans.rollback()
    await connection.close()
