import json
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.session import get_session
from app.main import app
from tests.fixtures.build_fixtures import build_all_fixtures, fixtures_dir


@pytest.fixture(scope="session", autouse=True)
def _ensure_fixtures() -> None:
    build_all_fixtures()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _override_get_session(
    test_session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[None]:
    """Override get_session to use the test engine so ASGI requests share the same DB."""

    async def _test_get_session() -> AsyncIterator[AsyncSession]:
        async with test_session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = _test_get_session
    yield
    app.dependency_overrides.pop(get_session, None)


def _sample_report_dict() -> dict:  # type: ignore[type-arg]
    from app.analysis.pipeline import build_report
    from app.parsing.frames import parse_frames
    from app.parsing.zip_loader import load_zip

    f = parse_frames(load_zip(fixtures_dir() / "happy.zip", max_bytes=50 * 1024 * 1024))
    return json.loads(build_report(f).model_dump_json(by_alias=True))


@pytest.mark.asyncio
async def test_share_creates_row_and_returns_id(_create_schema: None) -> None:
    payload = {"report": _sample_report_dict()}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/share", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert data["url"].startswith("/r/")
    assert "expires_at" in data


@pytest.mark.asyncio
async def test_share_rejects_invalid_report(_create_schema: None) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/share", json={"report": {"schema_version": 1}})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_shared_report_round_trip(_create_schema: None) -> None:
    payload = {"report": _sample_report_dict()}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post("/share", json=payload)
        share_id = create_resp.json()["id"]
        get_resp = await client.get(f"/r/{share_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["schema_version"] == 1


@pytest.mark.asyncio
async def test_get_shared_report_404(_create_schema: None) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/r/doesnotexist")
    assert resp.status_code == 404
