from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class GetUserInfoIn(BaseModel):
    telegram_user_id: int | None = None
    telegram_user_name: str | None = None
    user_id: str | None = None


class TrackTeacherOut(BaseModel):
    user_id: str
    display_name: str
    telegram_username: str | None = None


class TrackWithTeachersOut(BaseModel):
    track_id: str
    title: str
    status: str
    teachers: List[TrackTeacherOut] = Field(default_factory=list)


class CuratorOut(BaseModel):
    user_id: str | None = None
    display_name: str | None = None
    telegram_username: str | None = None


class UserInfoOut(BaseModel):
    user_id: str
    display_name: str
    telegram_id: int | None = None
    telegram_username: str | None = None
    telegram_login_name: str | None = None
    curator: CuratorOut
    active_tracks: List[TrackWithTeachersOut] = Field(default_factory=list)


class UserListItem(BaseModel):
    user_id: str
    display_name: str
    telegram_id: int | None = None
    telegram_username: str | None = None
    web_login: str | None = None
    last_seen_at: str | None = None


class UserListOut(BaseModel):
    total: int
    items: List[UserListItem]
