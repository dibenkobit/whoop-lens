import io

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.fixtures.build_fixtures import build_all_fixtures, fixtures_dir


@pytest.fixture(scope="session", autouse=True)
def _ensure_fixtures() -> None:
    build_all_fixtures()


@pytest.mark.asyncio
async def test_analyze_happy() -> None:
    zip_bytes = (fixtures_dir() / "happy.zip").read_bytes()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/analyze",
            files={"file": ("my_whoop_data.zip", zip_bytes, "application/zip")},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["schema_version"] == 1
    assert data["dials"]["recovery"]["unit"] == "%"


@pytest.mark.asyncio
async def test_analyze_corrupt_zip() -> None:
    zip_bytes = (fixtures_dir() / "corrupt.zip").read_bytes()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/analyze",
            files={"file": ("bad.zip", zip_bytes, "application/zip")},
        )
    assert resp.status_code == 400
    assert resp.json()["code"] in ("not_a_zip", "corrupt_zip")


@pytest.mark.asyncio
async def test_analyze_wrong_format() -> None:
    zip_bytes = (fixtures_dir() / "wrong_format.zip").read_bytes()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/analyze",
            files={"file": ("wrong.zip", zip_bytes, "application/zip")},
        )
    assert resp.status_code == 400
    assert resp.json()["code"] == "unexpected_schema"


@pytest.mark.asyncio
async def test_analyze_no_workouts_succeeds() -> None:
    zip_bytes = (fixtures_dir() / "no_workouts.zip").read_bytes()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/analyze",
            files={"file": ("nw.zip", zip_bytes, "application/zip")},
        )
    assert resp.status_code == 200
    assert resp.json()["workouts"] is None


@pytest.mark.asyncio
async def test_analyze_oversize() -> None:
    big = b"\x00" * (51 * 1024 * 1024)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/analyze",
            files={"file": ("big.zip", big, "application/zip")},
        )
    assert resp.status_code == 413
