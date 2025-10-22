from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from ..config import SESSION_MAX_TTL_MINUTES, SESSION_MIN_TTL_MINUTES


class SessionConnectIn(BaseModel):
    telegram_user_id: int
    telegram_username: str | None = None
    telegram_login_name: str | None = None
    display_name: str | None = None
    session_type: Literal["bot", "web", "admin"] = "bot"
    user_agent: str | None = None
    ip_hash: str | None = None
    ttl_minutes: int = Field(1440, ge=SESSION_MIN_TTL_MINUTES, le=SESSION_MAX_TTL_MINUTES)


class SessionRefreshIn(BaseModel):
    session_id: str
    ttl_minutes: int = Field(1440, ge=SESSION_MIN_TTL_MINUTES, le=SESSION_MAX_TTL_MINUTES)


class SessionDisconnectIn(BaseModel):
    session_id: str


class SessionOut(BaseModel):
    session_id: str
    user_id: str
    expires_at: str
    created_user: bool


class MiniAppConnectIn(BaseModel):
    telegram_user_id: int
    telegram_username: str | None = None
    telegram_login_name: str | None = None
    display_name: str | None = None
    init_data: str
    user_agent: str | None = None
    ip_hash: str | None = None
    ttl_minutes: int = Field(1440, ge=SESSION_MIN_TTL_MINUTES, le=SESSION_MAX_TTL_MINUTES)


class MiniAppConnectOut(BaseModel):
    client_token: str
    user_id: str
    telegram_user_id: int
    expires_at: str


class ClientTokenRevokeOut(BaseModel):
    ok: bool = True


class ClientTokenRefreshIn(BaseModel):
    ttl_minutes: int | None = Field(
        default=None,
        ge=SESSION_MIN_TTL_MINUTES,
        le=SESSION_MAX_TTL_MINUTES,
    )


class ClientTokenRefreshOut(BaseModel):
    expires_at: str
