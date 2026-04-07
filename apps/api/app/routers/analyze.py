import uuid
from typing import Annotated

from fastapi import APIRouter, File, UploadFile, status
from fastapi.responses import JSONResponse

from app.analysis.pipeline import build_report
from app.logging_config import get_logger
from app.parsing.errors import (
    CorruptZipError,
    FileTooLargeError,
    MissingRequiredFileError,
    NoDataError,
    NotAZipError,
    ParseError,
    UnexpectedSchemaError,
)
from app.parsing.frames import parse_frames
from app.parsing.zip_loader import load_zip
from app.settings import get_settings

router = APIRouter()
settings = get_settings()
log = get_logger(__name__)


@router.post("/analyze")
async def analyze(file: Annotated[UploadFile, File()]) -> JSONResponse:
    max_bytes = settings.max_upload_mb * 1024 * 1024

    # Stream into memory but enforce the cap
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(64 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"code": "file_too_large", "limit_mb": settings.max_upload_mb},
            )
        chunks.append(chunk)
    body = b"".join(chunks)

    import io

    try:
        loaded = load_zip(io.BytesIO(body), max_bytes=max_bytes)
        frames = parse_frames(loaded)
        report = build_report(frames)
    except FileTooLargeError as e:
        return JSONResponse(
            status_code=413,
            content={"code": e.code, "limit_mb": e.limit_mb},
        )
    except NotAZipError as e:
        return JSONResponse(status_code=400, content={"code": e.code})
    except CorruptZipError as e:
        return JSONResponse(status_code=400, content={"code": e.code})
    except MissingRequiredFileError as e:
        return JSONResponse(
            status_code=400, content={"code": e.code, "file": e.file}
        )
    except UnexpectedSchemaError as e:
        return JSONResponse(
            status_code=400,
            content={
                "code": e.code,
                "file": e.file,
                "missing_cols": e.missing,
                "extra_cols": e.extra,
            },
        )
    except NoDataError as e:
        return JSONResponse(
            status_code=400, content={"code": e.code, "file": e.file}
        )
    except ParseError as e:
        return JSONResponse(status_code=400, content={"code": e.code})
    except Exception:
        error_id = uuid.uuid4().hex
        log.exception("analysis_failed", error_id=error_id)
        return JSONResponse(
            status_code=500,
            content={"code": "analysis_failed", "error_id": error_id},
        )

    return JSONResponse(
        status_code=200, content=report.model_dump(mode="json", by_alias=True)
    )
