from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import SharedReport


@pytest.mark.asyncio
async def test_insert_and_select_shared_report(db_session: AsyncSession) -> None:
    report = {"hello": "world"}
    expires = datetime.now(UTC) + timedelta(days=30)
    db_session.add(SharedReport(id="abc12345", report=report, expires_at=expires))
    await db_session.flush()

    result = await db_session.execute(
        select(SharedReport).where(SharedReport.id == "abc12345")
    )
    row = result.scalar_one()
    assert row.report == {"hello": "world"}
    assert row.expires_at == expires
