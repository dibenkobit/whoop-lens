"""Time math used by sleep and trends analysis.

`bedtime_hour` maps an absolute datetime to a single number on a "day-aligned"
scale where 12:00-11:59 next day = 12.0-35.99. This makes "around midnight"
times statistically continuous instead of wrapping at 24.
"""
import math
from datetime import datetime


def bedtime_hour(dt: datetime) -> float:
    h = dt.hour + dt.minute / 60 + dt.second / 3600
    return h if h >= 12 else h + 24


def wake_hour(dt: datetime) -> float:
    return dt.hour + dt.minute / 60 + dt.second / 3600


def format_clock(h: float) -> str:
    h = h % 24
    hours = math.floor(h)
    minutes = round((h - hours) * 60)
    if minutes == 60:
        hours = (hours + 1) % 24
        minutes = 0
    return f"{hours:02d}:{minutes:02d}"
