from __future__ import annotations

from pydantic import BaseModel


class HealthResponse(BaseModel):
    ok: bool
    ts_utc: str
    ts_warsaw: str
    version: str
    build: str
    build_datetime: str
    generated_at: str
