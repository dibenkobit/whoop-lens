import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.cleanup import periodic_cleanup
from app.logging_config import configure_logging, get_logger
from app.routers import analyze, health, share
from app.settings import get_settings

settings = get_settings()
configure_logging(level=settings.log_level)
log = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    cleanup_task = asyncio.create_task(periodic_cleanup())
    log.info("lifespan_started")
    try:
        yield
    finally:
        cleanup_task.cancel()
        with suppress(asyncio.CancelledError):
            await cleanup_task
        log.info("lifespan_stopped")


app = FastAPI(title="Whoop Lens API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(analyze.router)
app.include_router(share.router)
app.include_router(health.router)


@app.get("/")
def root() -> dict[str, str]:
    return {"name": "whoop-lens-api", "version": "0.1.0"}
