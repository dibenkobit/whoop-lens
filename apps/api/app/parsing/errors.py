from typing import ClassVar


class ParseError(Exception):
    """Base class for all parsing errors that should become 400 responses."""

    code: ClassVar[str] = "parse_error"


class NotAZipError(ParseError):
    code = "not_a_zip"


class CorruptZipError(ParseError):
    code = "corrupt_zip"


class FileTooLargeError(ParseError):
    code = "file_too_large"

    def __init__(self, limit_mb: int) -> None:
        super().__init__(f"file larger than {limit_mb} MB")
        self.limit_mb = limit_mb


class MissingRequiredFileError(ParseError):
    code = "missing_required_file"

    def __init__(self, filename: str) -> None:
        super().__init__(f"missing required file: {filename}")
        self.file = filename


class UnexpectedSchemaError(ParseError):
    code = "unexpected_schema"

    def __init__(
        self,
        file: str,
        missing: list[str],
        extra: list[str],
    ) -> None:
        super().__init__(f"{file} has unexpected schema")
        self.file = file
        self.missing = missing
        self.extra = extra


class NoDataError(ParseError):
    code = "no_data"

    def __init__(self, filename: str) -> None:
        super().__init__(f"{filename} contains no data rows")
        self.file = filename
