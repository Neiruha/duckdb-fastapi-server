from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, constr


class TrackSummaryOut(BaseModel):
    track_id: str
    title: str
    owner_user_id: str
    status: str
    start_at: datetime | None = None
    end_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class TrackRenameIn(BaseModel):
    title: constr(strip_whitespace=True, min_length=1)


class TrackRenamedOut(BaseModel):
    track_id: str
    title: str
