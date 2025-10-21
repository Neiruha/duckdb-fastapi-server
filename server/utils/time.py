from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

__all__ = ["now_utc", "to_warsaw_iso", "ensure_naive_utc"]

_WARSAW = ZoneInfo("Europe/Warsaw")


def now_utc() -> datetime:
    """Return timezone-aware UTC timestamp."""

    return datetime.now(timezone.utc)


def to_warsaw_iso(dt: datetime) -> str:
    """Return ISO representation converted to Warsaw timezone."""

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(_WARSAW).isoformat()


def ensure_naive_utc(dt: datetime) -> datetime:
    """Ensure the datetime is naive UTC for DuckDB compatibility."""

    if dt.tzinfo is None:
        return dt
    return dt.astimezone(timezone.utc).replace(tzinfo=None)
