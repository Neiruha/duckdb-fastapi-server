from __future__ import annotations

import secrets
from datetime import timedelta

from fastapi import HTTPException, status

from ..config import MINIAPP_BOT_TOKEN
from ..db import client_tokens_repo, flags_repo, sessions_repo, users_repo
from ..middleware.access import Caller
from ..schemas.sessions import (
    ClientTokenRefreshIn,
    ClientTokenRefreshOut,
    ClientTokenRevokeOut,
    MiniAppConnectIn,
    MiniAppConnectOut,
    SessionConnectIn,
    SessionDisconnectIn,
    SessionOut,
    SessionRefreshIn,
)
from ..utils.telegram import TelegramInitDataError, parse_webapp_init_data
from ..utils.time import ensure_naive_utc, now_utc, to_warsaw_iso
from .sys_events_service import write_sys_event

_DEFAULT_CLIENT_TTL_MINUTES = 1440


def connect_session(payload: SessionConnectIn) -> SessionOut:
    user = users_repo.get_by_telegram_id(payload.telegram_user_id)
    created_user = False
    if not user:
        display_name = payload.display_name or f"tg:{payload.telegram_user_id}"
        user = users_repo.create_user_for_telegram(
            telegram_user_id=payload.telegram_user_id,
            display_name=display_name,
            telegram_username=payload.telegram_username,
            telegram_login_name=payload.telegram_login_name,
        )
        created_user = True
        write_sys_event(
            event_type="user_created",
            subject_user_id=user["user_id"],
            context="via sessions/connect",
        )
        write_sys_event(
            event_type="user_frozen",
            subject_user_id=user["user_id"],
            context="via sessions/connect",
        )

    session_row = sessions_repo.create_session(
        user_id=user["user_id"],
        session_type=payload.session_type,
        ttl_minutes=payload.ttl_minutes,
        user_agent=payload.user_agent,
        ip_hash=payload.ip_hash,
    )

    expires = session_row["expires_at"]
    expires_iso = to_warsaw_iso(expires)

    return SessionOut(
        session_id=session_row["session_id"],
        user_id=user["user_id"],
        expires_at=expires_iso,
        created_user=created_user,
    )


def refresh_session(payload: SessionRefreshIn) -> SessionOut:
    session = sessions_repo.get_session(payload.session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session.get("revoked_at"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session revoked")
    current_naive = ensure_naive_utc(now_utc())
    if session["expires_at"] < current_naive:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session expired")

    refreshed = sessions_repo.refresh_session(payload.session_id, payload.ttl_minutes)
    if not refreshed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    expires_iso = to_warsaw_iso(refreshed["expires_at"])
    return SessionOut(
        session_id=refreshed["session_id"],
        user_id=refreshed["user_id"],
        expires_at=expires_iso,
        created_user=False,
    )


def disconnect_session(payload: SessionDisconnectIn) -> dict:
    success = sessions_repo.revoke_session(payload.session_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return {"ok": True}


def connect_miniapp_session(payload: MiniAppConnectIn) -> MiniAppConnectOut:
    if not MINIAPP_BOT_TOKEN:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Mini app authentication disabled")

    try:
        init_payload = parse_webapp_init_data(payload.init_data, MINIAPP_BOT_TOKEN)
    except TelegramInitDataError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid init data signature") from exc

    if flags_repo.get_ban_by_telegram(payload.telegram_user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    user = users_repo.get_by_telegram_id(payload.telegram_user_id)
    if not user:
        display_name = payload.display_name or f"tg:{payload.telegram_user_id}"
        user = users_repo.create_user_for_telegram(
            telegram_user_id=payload.telegram_user_id,
            display_name=display_name,
            telegram_username=payload.telegram_username,
            telegram_login_name=payload.telegram_login_name,
        )
        write_sys_event(
            event_type="user_created",
            subject_user_id=user["user_id"],
            context="via sessions/connect/miniapp",
        )
        write_sys_event(
            event_type="user_frozen",
            subject_user_id=user["user_id"],
            context="via sessions/connect/miniapp",
        )
    else:
        if flags_repo.get_ban_by_user(user["user_id"]):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    if user.get("frozen"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ваш аккаунт заморожен администратором.",
        )

    ttl_minutes = payload.ttl_minutes
    now = now_utc()
    expires_at = now + timedelta(minutes=ttl_minutes)

    token_id = f"ct_{secrets.token_hex(12)}"
    client_tokens_repo.create_token(
        token_id=token_id,
        user_id=user["user_id"],
        telegram_user_id=payload.telegram_user_id,
        expires_at=expires_at,
        user_agent=payload.user_agent,
        ip_hash=payload.ip_hash,
        payload_json=init_payload,
    )

    write_sys_event(
        event_type="client_token_issued",
        subject_user_id=user["user_id"],
        context="via sessions/connect/miniapp",
    )

    return MiniAppConnectOut(
        client_token=token_id,
        user_id=user["user_id"],
        telegram_user_id=payload.telegram_user_id,
        expires_at=to_warsaw_iso(expires_at),
    )


def revoke_client_token(caller: Caller) -> ClientTokenRevokeOut:
    if not caller.token_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported token")

    client_tokens_repo.revoke_token(caller.token_id)
    if caller.user_id:
        write_sys_event(
            event_type="client_token_revoked",
            subject_user_id=caller.user_id,
            context="client/revoke",
        )
    return ClientTokenRevokeOut(ok=True)


def refresh_client_token(caller: Caller, payload: ClientTokenRefreshIn) -> ClientTokenRefreshOut:
    if not caller.token_id or not caller.user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported token")

    ttl_minutes = payload.ttl_minutes or _DEFAULT_CLIENT_TTL_MINUTES
    now = now_utc()
    new_expires = now + timedelta(minutes=ttl_minutes)

    refreshed = client_tokens_repo.refresh_token(caller.token_id, new_expires_at=new_expires)
    if not refreshed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    write_sys_event(
        event_type="client_token_refreshed",
        subject_user_id=caller.user_id,
        context="client/refresh",
    )

    expires_at = refreshed.get("expires_at", ensure_naive_utc(new_expires))
    return ClientTokenRefreshOut(expires_at=to_warsaw_iso(expires_at))
