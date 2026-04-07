from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from nanoid import generate as nanoid_generate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import SharedReport
from app.db.session import get_session
from app.models.report import WhoopReport
from app.models.share import ShareCreateRequest, ShareCreateResponse
from app.settings import get_settings

router = APIRouter()
settings = get_settings()


@router.post(
    "/share", response_model=ShareCreateResponse, status_code=status.HTTP_201_CREATED
)
async def create_share(
    req: ShareCreateRequest,
    session: AsyncSession = Depends(get_session),
) -> ShareCreateResponse:
    short_id = nanoid_generate(size=8)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.share_ttl_days)
    row = SharedReport(
        id=short_id,
        report=req.report.model_dump(mode="json", by_alias=True),
        expires_at=expires_at,
    )
    session.add(row)
    await session.commit()
    return ShareCreateResponse(id=short_id, url=f"/r/{short_id}", expires_at=expires_at)


@router.get("/r/{share_id}", response_model=WhoopReport)
async def get_shared_report(
    share_id: str,
    session: AsyncSession = Depends(get_session),
) -> WhoopReport:
    row = (
        await session.execute(
            select(SharedReport).where(SharedReport.id == share_id)
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="not found")
    if row.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=404, detail="expired")
    return WhoopReport.model_validate(row.report)
