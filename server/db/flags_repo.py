from __future__ import annotations

from typing import Dict, Optional

from .connection import dictrows, get_conn
from ..logging_utils import get_logger

log = get_logger("db.flags")


def get_ban_by_telegram(telegram_user_id: int) -> Optional[Dict[str, object]]:
    with get_conn(True) as con:
        cur = con.execute(
            "SELECT ban_id, user_id, telegram_user_id FROM banned_users WHERE telegram_user_id = ? LIMIT 1",
            [telegram_user_id],
        )
        rows = dictrows(cur)
    return rows[0] if rows else None


def get_ban_by_user(user_id: str) -> Optional[Dict[str, object]]:
    with get_conn(True) as con:
        cur = con.execute(
            "SELECT ban_id, user_id, telegram_user_id FROM banned_users WHERE user_id = ? LIMIT 1",
            [user_id],
        )
        rows = dictrows(cur)
    return rows[0] if rows else None
