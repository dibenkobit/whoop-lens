from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session

router = APIRouter()


@router.get("/healthz")
async def healthz(session: AsyncSession = Depends(get_session)) -> dict[str, object]:
    try:
        await session.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "down"
    return {"ok": db_status == "ok", "db": db_status}
