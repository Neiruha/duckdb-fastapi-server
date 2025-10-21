from __future__ import annotations

from datetime import timedelta
from typing import Any, Dict, Optional

from .connection import dictrows, get_conn
from ..logging_utils import get_logger
from ..utils.ids import new_id
from ..utils.time import ensure_naive_utc, now_utc

log = get_logger("db.sessions")


def create_session(
    *,
    user_id: str,
    session_type: str,
    ttl_minutes: int,
    user_agent: str | None,
    ip_hash: str | None,
) -> Dict[str, Any]:
    session_id = new_id("ses_")
    now = now_utc()
    expires = now + timedelta(minutes=ttl_minutes)
    with get_conn(False) as con:
        con.execute(
            """
            INSERT INTO sessions (session_id, user_id, created_at, expires_at, ip_hash, user_agent, session_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                session_id,
                user_id,
                ensure_naive_utc(now),
                ensure_naive_utc(expires),
                ip_hash,
                user_agent,
                session_type,
            ],
        )
        cur = con.execute(
            "SELECT session_id, user_id, created_at, expires_at FROM sessions WHERE session_id = ?",
            [session_id],
        )
        row = dictrows(cur)[0]
    log.info("Created session %s for user %s", session_id, user_id)
    return row


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    with get_conn(True) as con:
        cur = con.execute(
            """
            SELECT session_id, user_id, created_at, expires_at, revoked_at
            FROM sessions
            WHERE session_id = ?
            LIMIT 1
            """,
            [session_id],
        )
        rows = dictrows(cur)
    return rows[0] if rows else None


def refresh_session(session_id: str, ttl_minutes: int) -> Optional[Dict[str, Any]]:
    now = now_utc()
    expires = now + timedelta(minutes=ttl_minutes)
    with get_conn(False) as con:
        cur = con.execute(
            """
            UPDATE sessions
            SET expires_at = ?, revoked_at = NULL
            WHERE session_id = ?
            """,
            [ensure_naive_utc(expires), session_id],
        )
        if cur.rowcount == 0:
            return None
        cur = con.execute(
            "SELECT session_id, user_id, created_at, expires_at, revoked_at FROM sessions WHERE session_id = ?",
            [session_id],
        )
        rows = dictrows(cur)
    log.info("Refreshed session %s", session_id)
    return rows[0]


def revoke_session(session_id: str) -> bool:
    with get_conn(False) as con:
        cur = con.execute(
            "UPDATE sessions SET revoked_at = CURRENT_TIMESTAMP WHERE session_id = ? AND revoked_at IS NULL",
            [session_id],
        )
        changed = cur.rowcount
    if changed:
        log.info("Revoked session %s", session_id)
    return bool(changed)


def last_seen_at(user_id: str) -> Optional[Any]:
    with get_conn(True) as con:
        cur = con.execute(
            "SELECT MAX(created_at) FROM sessions WHERE user_id = ?",
            [user_id],
        )
        row = cur.fetchone()
    return row[0] if row else None
