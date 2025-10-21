from __future__ import annotations

from fastapi import HTTPException, status

from ..db import sessions_repo, users_repo
from ..schemas.sessions import SessionConnectIn, SessionDisconnectIn, SessionOut, SessionRefreshIn
from ..utils.time import ensure_naive_utc, now_utc, to_warsaw_iso
from .sys_events_service import write_sys_event


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
