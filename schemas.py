# /srv/neiruha/lab/app/server/schemas.py
from typing import Optional, List
from pydantic import BaseModel, Field

# ---------- ВХОД ----------
class GetUserInfoIn(BaseModel):
    telegram_user_id: Optional[int] = Field(None)
    telegram_user_name: Optional[str] = Field(None)
    user_id: Optional[str] = Field(None)

# ---------- ВЫХОД ----------
class TeacherOut(BaseModel):
    user_id: str
    display_name: str
    telegram_username: Optional[str] = None

class TrackOut(BaseModel):
    track_id: str
    title: str
    status: str
    teachers: List[TeacherOut] = []

class CuratorOut(BaseModel):
    user_id: Optional[str] = None
    display_name: Optional[str] = None
    telegram_username: Optional[str] = None

class UserInfoOut(BaseModel):
    user_id: str
    display_name: str
    telegram_id: Optional[int] = None
    telegram_username: Optional[str] = None
    telegram_login_name: Optional[str] = None
    curator: CuratorOut
    active_tracks: List[TrackOut]

class UserListItem(BaseModel):
    user_id: str
    display_name: str
    telegram_id: Optional[int] = None
    telegram_username: Optional[str] = None
    web_login: Optional[str] = None
    last_seen_at: Optional[str] = None

class UserListOut(BaseModel):
    total: int
    items: List[UserListItem]
