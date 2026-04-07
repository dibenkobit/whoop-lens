import asyncio
from datetime import datetime, timezone
from typing import cast

from sqlalchemy import delete
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import SharedReport
from app.db.session import SessionFactory
from app.logging_config import get_logger

log = get_logger(__name__)
CLEANUP_INTERVAL_SECONDS = 6 * 60 * 60


async def delete_expired_now(session: AsyncSession | None = None) -> int:
    """Run a single delete pass. Returns rows deleted. Useful in tests.

    If *session* is provided it is used directly (no commit — caller manages
    the transaction).  If omitted a fresh session from SessionFactory is used
    and committed before returning.
    """
    stmt = delete(SharedReport).where(
        SharedReport.expires_at < datetime.now(timezone.utc)
    )
    if session is not None:
        result = cast(CursorResult[tuple[()]], await session.execute(stmt))
        await session.flush()
        return int(result.rowcount or 0)
    async with SessionFactory() as s:
        result = cast(CursorResult[tuple[()]], await s.execute(stmt))
        await s.commit()
        return int(result.rowcount or 0)


async def periodic_cleanup() -> None:
    while True:
        try:
            n = await delete_expired_now()
            log.info("cleanup_ran", deleted=n)
        except Exception:  # noqa: BLE001
            log.exception("cleanup_failed")
        await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
