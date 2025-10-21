from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field

from .tracks import TrackSummaryOut
from .users import CuratorOut, TrackWithTeachersOut


class ProfileUserOut(BaseModel):
    user_id: str
    display_name: str
    telegram_id: int | None = None
    telegram_username: str | None = None
    telegram_login_name: str | None = None
    frozen: bool
    banned: bool
    roles: List[str] = Field(default_factory=list)
    mentor_user_id: str | None = None
    curator: CuratorOut | None = None


class ProfileByTelegramOut(BaseModel):
    user: ProfileUserOut | None = None
    tracks_active_as_student: List[TrackWithTeachersOut] = Field(default_factory=list)
    tracks_active_as_teacher: List[TrackSummaryOut] = Field(default_factory=list)
    last_seen_at: str | None = None
