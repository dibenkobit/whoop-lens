from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.cleanup import delete_expired_now
from app.db.models import SharedReport


@pytest.mark.asyncio
async def test_cleanup_removes_only_expired(db_session: AsyncSession) -> None:
    now = datetime.now(timezone.utc)
    db_session.add(
        SharedReport(id="alive001", report={"x": 1}, expires_at=now + timedelta(days=1))
    )
    db_session.add(
        SharedReport(id="dead0001", report={"x": 1}, expires_at=now - timedelta(days=1))
    )
    await db_session.flush()

    deleted = await delete_expired_now(session=db_session)
    assert deleted >= 1

    rows = (await db_session.execute(select(SharedReport))).scalars().all()
    ids = {r.id for r in rows}
    assert "alive001" in ids
    assert "dead0001" not in ids
