from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

import json

from .connection import dictrows, get_conn
from ..logging_utils import get_logger
from ..utils.time import ensure_naive_utc

log = get_logger("db.client_tokens")


def create_token(
    *,
    token_id: str,
    user_id: str,
    telegram_user_id: int,
    expires_at: datetime,
    user_agent: str | None,
    ip_hash: str | None,
    payload_json: Dict[str, Any] | None,
) -> Dict[str, Any]:
    with get_conn(False) as con:
        con.execute(
            """
            INSERT INTO client_tokens (
                token_id,
                user_id,
                telegram_user_id,
                token_hash,
                expires_at,
                user_agent,
                ip_hash,
                payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                token_id,
                user_id,
                telegram_user_id,
                "",
                ensure_naive_utc(expires_at),
                user_agent,
                ip_hash,
                json.dumps(payload_json) if payload_json is not None else None,
            ],
        )
        cur = con.execute(
            """
            SELECT token_id, user_id, telegram_user_id, issued_at, expires_at, revoked_at
            FROM client_tokens
            WHERE token_id = ?
            LIMIT 1
            """,
            [token_id],
        )
        row = dictrows(cur)[0]
    log.info("Issued client token %s for user %s", token_id, user_id)
    return row


def get_token(token_id: str) -> Optional[Dict[str, Any]]:
    with get_conn(True) as con:
        cur = con.execute(
            """
            SELECT
                ct.token_id,
                ct.user_id,
                ct.telegram_user_id,
                ct.expires_at,
                ct.revoked_at,
                u.frozen AS user_frozen,
                CASE WHEN bu.user_id IS NOT NULL THEN TRUE ELSE FALSE END AS user_banned
            FROM client_tokens ct
            LEFT JOIN users u ON u.user_id = ct.user_id
            LEFT JOIN banned_users bu ON bu.user_id = ct.user_id
            WHERE ct.token_id = ?
            LIMIT 1
            """,
            [token_id],
        )
        rows = dictrows(cur)
    return rows[0] if rows else None


def revoke_token(token_id: str) -> bool:
    with get_conn(False) as con:
        cur = con.execute(
            "UPDATE client_tokens SET revoked_at = CURRENT_TIMESTAMP WHERE token_id = ? AND revoked_at IS NULL",
            [token_id],
        )
        changed = cur.rowcount
    if changed:
        log.info("Revoked client token %s", token_id)
    return bool(changed)


def refresh_token(token_id: str, *, new_expires_at: datetime) -> Optional[Dict[str, Any]]:
    with get_conn(False) as con:
        cur = con.execute(
            """
            UPDATE client_tokens
            SET expires_at = ?, revoked_at = NULL
            WHERE token_id = ?
            """,
            [ensure_naive_utc(new_expires_at), token_id],
        )
        if cur.rowcount == 0:
            return None
        cur = con.execute(
            """
            SELECT token_id, user_id, telegram_user_id, expires_at, revoked_at
            FROM client_tokens
            WHERE token_id = ?
            LIMIT 1
            """,
            [token_id],
        )
        rows = dictrows(cur)
    log.info("Refreshed client token %s", token_id)
    return rows[0] if rows else None
