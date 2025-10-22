from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from .connection import dictrows, get_conn
from ..logging_utils import get_logger
from ..utils.ids import new_id

log = get_logger("db.messages")


def _serialize_data(data: Optional[Dict[str, Any]]) -> Optional[str]:
    if data is None:
        return None
    try:
        return json.dumps(data)
    except (TypeError, ValueError) as exc:
        raise ValueError("message data must be JSON serializable") from exc


def list_inbox(
    *,
    recipient_user_id: str,
    limit: int,
    offset: int,
    unread_only: bool,
    since: Optional[datetime],
    until: Optional[datetime],
) -> List[Dict[str, Any]]:
    where = ["mr.recipient_user_id = ?"]
    params: List[Any] = [recipient_user_id]
    if unread_only:
        where.append("COALESCE(mr.read_flag, FALSE) = FALSE")
    if since is not None:
        where.append("m.created_at >= ?")
        params.append(since)
    if until is not None:
        where.append("m.created_at <= ?")
        params.append(until)

    where_clause = " AND ".join(where)
    sql = f"""
        SELECT m.message_id,
               m.message_type,
               m.content,
               m.message_data_json,
               m.sender_user_id,
               m.created_at,
               mr.recipient_user_id,
               mr.read_flag
        FROM message_recipients mr
        JOIN messages m ON m.message_id = mr.message_id
        WHERE {where_clause}
        ORDER BY m.created_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])

    with get_conn(True) as con:
        cur = con.execute(sql, params)
        rows = dictrows(cur)
    return rows


def list_sent(
    *,
    sender_user_id: str,
    limit: int,
    offset: int,
    since: Optional[datetime],
    until: Optional[datetime],
) -> List[Dict[str, Any]]:
    where = ["m.sender_user_id = ?"]
    params: List[Any] = [sender_user_id]
    if since is not None:
        where.append("m.created_at >= ?")
        params.append(since)
    if until is not None:
        where.append("m.created_at <= ?")
        params.append(until)

    where_clause = " AND ".join(where)
    sql = f"""
        SELECT m.message_id,
               m.message_type,
               m.content,
               m.message_data_json,
               m.sender_user_id,
               m.created_at,
               mr.recipient_user_id,
               mr.read_flag
        FROM messages m
        LEFT JOIN message_recipients mr ON mr.message_id = m.message_id
        WHERE {where_clause}
        ORDER BY m.created_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])

    with get_conn(True) as con:
        cur = con.execute(sql, params)
        rows = dictrows(cur)
    return rows


def insert_message(
    *,
    sender_user_id: Optional[str],
    recipient_user_id: str,
    recipient_telegram_user_id: Optional[int],
    message_type: str,
    content: Optional[str],
    message_data: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    message_id = new_id("msg_")
    serialized = _serialize_data(message_data)
    with get_conn(False) as con:
        con.execute(
            """
            INSERT INTO messages (
                message_id,
                message_type,
                sender_user_id,
                telegram_user_id,
                content,
                message_data_json,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            [
                message_id,
                message_type,
                sender_user_id,
                recipient_telegram_user_id,
                content,
                serialized,
            ],
        )
        con.execute(
            """
            INSERT INTO message_recipients (
                message_id,
                recipient_user_id,
                read_flag,
                read_at
            )
            VALUES (?, ?, FALSE, NULL)
            """,
            [message_id, recipient_user_id],
        )

    log.info(
        "Inserted message %s from %s to %s", message_id, sender_user_id, recipient_user_id
    )
    return {"message_id": message_id, "recipient_user_id": recipient_user_id}


def mark_read(
    *,
    message_ids: List[str],
    recipient_user_id: Optional[str] = None,
) -> int:
    if not message_ids:
        return 0

    placeholders = ", ".join(["?"] * len(message_ids))
    sql = f"""
        UPDATE message_recipients
        SET read_flag = TRUE,
            read_at = CURRENT_TIMESTAMP
        WHERE message_id IN ({placeholders})
    """
    params: List[Any] = list(message_ids)
    if recipient_user_id is not None:
        sql += " AND recipient_user_id = ?"
        params.append(recipient_user_id)

    with get_conn(False) as con:
        cur = con.execute(sql, params)
        updated = cur.rowcount

    log.info("Marked %s messages read for %s", updated, recipient_user_id or "*")
    return int(updated)
