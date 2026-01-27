from __future__ import annotations

from typing import List, Literal

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


ProfileType = Literal["header", "tracks", "full", "charts", "disc_profile"]


class ProfileHeaderOut(BaseModel):
    user_id: str
    display_name: str
    telegram_id: int | None = None
    telegram_username: str | None = None
    telegram_login_name: str | None = None
    telegram_photo_url: str | None = None
    frozen: bool
    banned: bool
    roles: List[str] = Field(default_factory=list)
    mentor_user_id: str | None = None
    curator: CuratorOut | None = None


class ProfileTrackOut(BaseModel):
    track_id: str
    title: str
    status: str
    owner_user_id: str
    role_in_track: str
    joined_at: str | None = None


class ProfileResponseOut(BaseModel):
    profile_type: ProfileType
    header: ProfileHeaderOut | None = None
    tracks: List[ProfileTrackOut] = Field(default_factory=list)
