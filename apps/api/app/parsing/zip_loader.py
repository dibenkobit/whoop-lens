import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

from app.parsing.csv_schema import CsvFile
from app.parsing.errors import (
    CorruptZipError,
    FileTooLargeError,
    MissingRequiredFileError,
    NotAZipError,
)

REQUIRED_FILES: frozenset[CsvFile] = frozenset({CsvFile.CYCLES, CsvFile.SLEEPS})
OPTIONAL_FILES: frozenset[CsvFile] = frozenset({CsvFile.WORKOUTS, CsvFile.JOURNAL})

MAX_EXTRACTED_BYTES = 200 * 1024 * 1024  # 200 MB total uncompressed cap


@dataclass(frozen=True)
class LoadedZip:
    files: dict[CsvFile, bytes]


def load_zip(source: Path | BinaryIO, *, max_bytes: int) -> LoadedZip:
    """Load a Whoop export ZIP and return its CSV files as bytes.

    Raises ParseError subclasses for any failure mode.
    """
    if isinstance(source, Path):
        size = source.stat().st_size
        if size > max_bytes:
            raise FileTooLargeError(limit_mb=max_bytes // (1024 * 1024))
        opener: object = source
    else:
        opener = source

    try:
        zf = zipfile.ZipFile(opener)
    except zipfile.BadZipFile as e:
        # distinguish "not a zip" from "corrupt zip"
        if isinstance(opener, Path):
            head = opener.read_bytes()[:4]
        else:
            opener.seek(0)
            head = opener.read(4)
            opener.seek(0)
        if not head.startswith(b"PK"):
            raise NotAZipError(str(e)) from e
        raise CorruptZipError(str(e)) from e

    try:
        names = {name.lower(): name for name in zf.namelist()}
        files: dict[CsvFile, bytes] = {}
        total_bytes = 0
        for csv_file in CsvFile:
            actual_name = names.get(csv_file.value.lower())
            if actual_name is None:
                if csv_file in REQUIRED_FILES:
                    raise MissingRequiredFileError(csv_file.value)
                continue
            with zf.open(actual_name) as f:
                content = f.read(MAX_EXTRACTED_BYTES + 1)
            if len(content) > MAX_EXTRACTED_BYTES:
                raise CorruptZipError("uncompressed payload exceeds 200 MB")
            total_bytes += len(content)
            if total_bytes > MAX_EXTRACTED_BYTES:
                raise CorruptZipError("uncompressed payload exceeds 200 MB")
            files[csv_file] = content

        # Always include the optional files (empty if missing) so consumers
        # don't have to KeyError-check.
        for csv_file in OPTIONAL_FILES:
            files.setdefault(csv_file, b"")

        return LoadedZip(files=files)
    finally:
        zf.close()
