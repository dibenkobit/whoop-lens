from datetime import datetime

from pydantic import BaseModel

from app.models.report import WhoopReport


class ShareCreateRequest(BaseModel):
    report: WhoopReport


class ShareCreateResponse(BaseModel):
    id: str
    url: str
    expires_at: datetime
