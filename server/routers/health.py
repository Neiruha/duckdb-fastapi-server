from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter
from zoneinfo import ZoneInfo

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    now_utc = datetime.now(timezone.utc)
    now_warsaw = datetime.now(ZoneInfo("Europe/Warsaw"))
    return {
        "ok": True,
        "ts_utc": now_utc.isoformat(),
        "ts_warsaw": now_warsaw.isoformat(),
    }
