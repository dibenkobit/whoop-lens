from datetime import datetime

import pytest

from app.analysis.time_helpers import bedtime_hour, format_clock, wake_hour


@pytest.mark.parametrize(
    ("dt", "expected"),
    [
        (datetime(2025, 1, 1, 23, 30), 23.5),
        (datetime(2025, 1, 2, 1, 0), 25.0),
        (datetime(2025, 1, 2, 4, 45), 28.75),
        (datetime(2025, 1, 1, 12, 0), 12.0),
    ],
)
def test_bedtime_hour(dt: datetime, expected: float) -> None:
    assert bedtime_hour(dt) == pytest.approx(expected)


def test_wake_hour() -> None:
    assert wake_hour(datetime(2025, 1, 2, 9, 30)) == pytest.approx(9.5)


@pytest.mark.parametrize(
    ("h", "expected"),
    [
        (23.5, "23:30"),
        (25.0, "01:00"),
        (28.75, "04:45"),
    ],
)
def test_format_clock(h: float, expected: str) -> None:
    assert format_clock(h) == expected
