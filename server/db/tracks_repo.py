from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from .connection import dictrows, get_conn
from ..logging_utils import get_logger

log = get_logger("db.tracks")


def list_by_teacher(user_id: str, active_only: bool, now: datetime) -> List[Dict[str, Any]]:
    params: List[Any] = [user_id]
    sql = [
        "SELECT t.track_id, t.title, t.status,",
        "       NULL AS start_at, NULL AS end_at,",
        "       t.owner_user_id, t.created_at, t.updated_at",
        "FROM track_participants tp",
        "JOIN tracks t ON t.track_id = tp.track_id",
        "WHERE tp.user_id = ? AND tp.role_in_track = 'teacher'",
    ]
    if active_only:
        sql.append("AND t.status = 'active'")
    sql.append("ORDER BY t.created_at DESC")
    query = "\n".join(sql)
    with get_conn(True) as con:
        cur = con.execute(query, params)
        rows = dictrows(cur)
    return rows


def list_by_student(user_id: str, active_only: bool, now: datetime) -> List[Dict[str, Any]]:
    params: List[Any] = [user_id]
    sql = [
        "SELECT t.track_id, t.title, t.status,",
        "       NULL AS start_at, NULL AS end_at,",
        "       t.owner_user_id, t.created_at, t.updated_at",
        "FROM track_participants tp",
        "JOIN tracks t ON t.track_id = tp.track_id",
        "WHERE tp.user_id = ? AND tp.role_in_track = 'student'",
    ]
    if active_only:
        sql.append("AND t.status = 'active'")
    sql.append("ORDER BY t.created_at DESC")
    query = "\n".join(sql)
    with get_conn(True) as con:
        cur = con.execute(query, params)
        rows = dictrows(cur)
    return rows


def list_teachers_for_track(track_id: str) -> List[Dict[str, Any]]:
    with get_conn(True) as con:
        cur = con.execute(
            """
            SELECT u.user_id, u.display_name, u.telegram_username
            FROM track_participants tp
            JOIN users u ON u.user_id = tp.user_id
            WHERE tp.track_id = ? AND tp.role_in_track = 'teacher'
            ORDER BY tp.joined_at ASC
            """,
            [track_id],
        )
        rows = dictrows(cur)
    return rows


def list_tracks_for_user(user_id: str) -> List[Dict[str, Any]]:
    with get_conn(True) as con:
        cur = con.execute(
            """
            SELECT t.track_id,
                   t.title,
                   t.status,
                   t.owner_user_id,
                   tp.role_in_track,
                   tp.joined_at
            FROM track_participants tp
            JOIN tracks t ON t.track_id = tp.track_id
            WHERE tp.user_id = ?
            ORDER BY tp.joined_at DESC
            """,
            [user_id],
        )
        rows = dictrows(cur)
    return rows


