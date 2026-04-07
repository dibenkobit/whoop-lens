from fastapi import FastAPI

from app.logging_config import configure_logging, get_logger
from app.routers import analyze, share
from app.settings import get_settings

settings = get_settings()
configure_logging(level=settings.log_level)
log = get_logger(__name__)

app = FastAPI(title="Whoop Lens API", version="0.1.0")
app.include_router(analyze.router)
app.include_router(share.router)


@app.get("/")
def root() -> dict[str, str]:
    return {"name": "whoop-lens-api", "version": "0.1.0"}
