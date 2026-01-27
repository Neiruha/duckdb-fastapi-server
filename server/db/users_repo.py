from __future__ import annotations

from typing import Any, Dict, List, Optional

from .connection import dictrows, get_conn
from ..logging_utils import get_logger
from ..utils.ids import new_id

log = get_logger("db.users")


def find_user(
    user_id: Optional[str],
    telegram_user_id: Optional[int],
    telegram_user_name: Optional[str],
) -> Optional[Dict[str, Any]]:
    where: List[str] = []
    params: List[Any] = []
    if user_id:
        where.append("u.user_id = ?")
        params.append(user_id)
    if telegram_user_id is not None:
        where.append("u.telegram_id = ?")
        params.append(telegram_user_id)
    if telegram_user_name:
        where.append("(u.telegram_username = ? OR u.telegram_login_name = ?)")
        params.extend([telegram_user_name, telegram_user_name])

    if not where:
        log.warning("find_user called without identifiers")
        return None

    sql = f"""
        SELECT u.user_id, u.display_name, u.telegram_id, u.telegram_username,
               u.telegram_login_name, u.mentor_user_id, u.frozen
        FROM users u
        WHERE {" OR ".join(where)}
        LIMIT 1
    """
    with get_conn(True) as con:
        cur = con.execute(sql, params)
        rows = dictrows(cur)
    return rows[0] if rows else None


def get_by_telegram_id(telegram_user_id: int) -> Optional[Dict[str, Any]]:
    with get_conn(True) as con:
        cur = con.execute(
            """
            SELECT user_id, display_name, telegram_id, telegram_username,
                   telegram_login_name, telegram_photo_url, mentor_user_id,
                   frozen, created_at, updated_at
            FROM users
            WHERE telegram_id = ?
            LIMIT 1
            """,
            [telegram_user_id],
        )
        rows = dictrows(cur)
    return rows[0] if rows else None


def get_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    with get_conn(True) as con:
        cur = con.execute(
            """
            SELECT user_id, display_name, telegram_id, telegram_username,
                   telegram_login_name, telegram_photo_url, mentor_user_id,
                   frozen, created_at, updated_at
            FROM users
            WHERE user_id = ?
            LIMIT 1
            """,
            [user_id],
        )
        rows = dictrows(cur)
    return rows[0] if rows else None


def create_user_for_telegram(
    *,
    telegram_user_id: int,
    display_name: str,
    telegram_username: str | None,
    telegram_login_name: str | None,
) -> Dict[str, Any]:
    user_id = new_id("u_")
    with get_conn(False) as con:
        con.execute(
            """
            INSERT INTO users (
                user_id,
                display_name,
                telegram_id,
                telegram_username,
                telegram_login_name,
                frozen
            )
            VALUES (?, ?, ?, ?, ?, TRUE)
            """,
            [
                user_id,
                display_name,
                telegram_user_id,
                telegram_username,
                telegram_login_name,
            ],
        )
        cur = con.execute(
            """
            SELECT user_id, display_name, telegram_id, telegram_username,
                   telegram_login_name, mentor_user_id, frozen, created_at,
                   updated_at
            FROM users
            WHERE user_id = ?
            LIMIT 1
            """,
            [user_id],
        )
        row = dictrows(cur)[0]
    log.info("Created user %s for telegram %s", user_id, telegram_user_id)
    return row


def get_curator(mentor_user_id: Optional[str]) -> Optional[Dict[str, Any]]:
    if not mentor_user_id:
        return None
    with get_conn(True) as con:
        cur = con.execute(
            """
            SELECT user_id, display_name, telegram_username
            FROM users
            WHERE user_id = ?
            LIMIT 1
            """,
            [mentor_user_id],
        )
        rows = dictrows(cur)
    return rows[0] if rows else None


def get_roles(user_id: str) -> List[str]:
    with get_conn(True) as con:
        cur = con.execute(
            """
            SELECT role
            FROM user_roles
            WHERE user_id = ?
            ORDER BY role
            """,
            [user_id],
        )
        rows = cur.fetchall()
    return [row[0] for row in rows]


def is_frozen(user_id: str) -> bool:
    with get_conn(True) as con:
        cur = con.execute(
            "SELECT frozen FROM users WHERE user_id = ? LIMIT 1",
            [user_id],
        )
        row = cur.fetchone()
    return bool(row[0]) if row else False


def set_frozen(user_id: str, frozen: bool) -> None:
    with get_conn(False) as con:
        con.execute(
            "UPDATE users SET frozen = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
            [frozen, user_id],
        )
    log.info("Set frozen=%s for user %s", frozen, user_id)


def list_users(limit: int, offset: int) -> Dict[str, Any]:
    with get_conn(True) as con:
        sql = f"""
            WITH last_seen AS (
                SELECT user_id, MAX(created_at) AS last_seen_at
                FROM sessions
                GROUP BY user_id
            )
            SELECT u.user_id,
                   u.display_name,
                   u.telegram_id,
                   u.telegram_username,
                   u.web_login,
                   ls.last_seen_at
            FROM users u
            LEFT JOIN last_seen ls ON ls.user_id = u.user_id
            ORDER BY COALESCE(ls.last_seen_at, TIMESTAMP '1970-01-01') DESC, u.created_at DESC
            LIMIT {limit} OFFSET {offset}
        """
        cur = con.execute(sql)
        items = dictrows(cur)
        total = con.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    return {"total": total, "items": items}


def list_users_by_role(role: str, limit: int, offset: int) -> Dict[str, Any]:
    with get_conn(True) as con:
        sql = f"""
            WITH last_seen AS (
                SELECT user_id, MAX(created_at) AS last_seen_at
                FROM sessions
                GROUP BY user_id
            )
            SELECT u.user_id,
                   u.display_name,
                   u.telegram_id,
                   u.telegram_username,
                   u.web_login,
                   ls.last_seen_at
            FROM users u
            JOIN user_roles ur ON ur.user_id = u.user_id
            LEFT JOIN last_seen ls ON ls.user_id = u.user_id
            WHERE ur.role = ?
            ORDER BY COALESCE(ls.last_seen_at, TIMESTAMP '1970-01-01') DESC, u.created_at DESC
            LIMIT {limit} OFFSET {offset}
        """
        cur = con.execute(sql, [role])
        items = dictrows(cur)
        total = (
            con.execute(
                "SELECT COUNT(DISTINCT user_id) FROM user_roles WHERE role = ?",
                [role],
            ).fetchone()[0]
        )
    return {"total": total, "items": items}


def rename_display_name(user_id: str, display_name: str) -> Dict[str, Any] | None:
    with get_conn(False) as con:
        cur = con.execute(
            """
            UPDATE users
            SET display_name = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
            RETURNING user_id, display_name
            """,
            [display_name, user_id],
        )
        rows = dictrows(cur)
    return rows[0] if rows else None
