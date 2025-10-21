from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from .connection import dictrows, get_conn
from ..logging_utils import get_logger
from ..utils.time import ensure_naive_utc

log = get_logger("db.tracks")


def list_by_teacher(user_id: str, active_only: bool, now: datetime) -> List[Dict[str, Any]]:
    params: List[Any] = [user_id]
    sql = [
        "SELECT t.track_id, t.title, t.status, t.start_at, t.end_at,",
        "       t.owner_user_id, t.created_at, t.updated_at",
        "FROM track_participants tp",
        "JOIN tracks t ON t.track_id = tp.track_id",
        "WHERE tp.user_id = ? AND tp.role_in_track = 'teacher'",
    ]
    if active_only:
        sql.append("AND t.status = 'active'")
        sql.append("AND (t.start_at IS NULL OR t.start_at <= ?)")
        sql.append("AND (t.end_at IS NULL OR t.end_at > ?)")
        params.extend([ensure_naive_utc(now), ensure_naive_utc(now)])
    sql.append("ORDER BY t.created_at DESC")
    query = "\n".join(sql)
    with get_conn(True) as con:
        cur = con.execute(query, params)
        rows = dictrows(cur)
    return rows


def list_by_student(user_id: str, active_only: bool, now: datetime) -> List[Dict[str, Any]]:
    params: List[Any] = [user_id]
    sql = [
        "SELECT t.track_id, t.title, t.status, t.start_at, t.end_at,",
        "       t.owner_user_id, t.created_at, t.updated_at",
        "FROM track_participants tp",
        "JOIN tracks t ON t.track_id = tp.track_id",
        "WHERE tp.user_id = ? AND tp.role_in_track = 'student'",
    ]
    if active_only:
        sql.append("AND t.status = 'active'")
        sql.append("AND (t.start_at IS NULL OR t.start_at <= ?)")
        sql.append("AND (t.end_at IS NULL OR t.end_at > ?)")
        params.extend([ensure_naive_utc(now), ensure_naive_utc(now)])
    sql.append("ORDER BY t.created_at DESC")
    query = "\n".join(sql)
    with get_conn(True) as con:
        cur = con.execute(query, params)
        rows = dictrows(cur)
    return rows


def list_active(now: datetime) -> List[Dict[str, Any]]:
    with get_conn(True) as con:
        cur = con.execute(
            """
            SELECT track_id, title, owner_user_id, status, start_at, end_at, created_at, updated_at
            FROM tracks
            WHERE status = 'active'
              AND (start_at IS NULL OR start_at <= ?)
              AND (end_at IS NULL OR end_at > ?)
            ORDER BY created_at DESC
            """,
            [ensure_naive_utc(now), ensure_naive_utc(now)],
        )
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


def rename_title(track_id: str, title: str) -> Optional[Dict[str, Any]]:
    with get_conn(False) as con:
        cur = con.execute(
            """
            UPDATE tracks
            SET title = ?, updated_at = CURRENT_TIMESTAMP
            WHERE track_id = ?
            RETURNING track_id, title
            """,
            [title, track_id],
        )
        rows = dictrows(cur)
    return rows[0] if rows else None
