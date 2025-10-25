from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter
from zoneinfo import ZoneInfo

from ..config import BUILD_DATETIME, BUILD_NAME, SERVER_VERSION
from ..schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    now_utc = datetime.now(timezone.utc)
    now_warsaw = datetime.now(ZoneInfo("Europe/Warsaw"))
    iso_utc = now_utc.isoformat()
    return HealthResponse(
        ok=True,
        ts_utc=iso_utc,
        ts_warsaw=now_warsaw.isoformat(),
        version=SERVER_VERSION,
        build=BUILD_NAME or "unknown",
        build_datetime=BUILD_DATETIME or "unknown",
        generated_at=iso_utc,
    )
