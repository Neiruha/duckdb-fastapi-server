from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from .connection import dictrows, get_conn
from ..utils.time import ensure_naive_utc


def list_by_track(
    track_id: str,
    *,
    student_id: Optional[str] = None,
    metric_id: Optional[str] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    limit: int,
    offset: int,
) -> List[Dict[str, Any]]:
    where = ["s.track_id = ?"]
    params: List[Any] = [track_id]

    if student_id:
        where.append("s.student_id = ?")
        params.append(student_id)
    if metric_id:
        where.append("s.metric_id = ?")
        params.append(metric_id)
    if since:
        where.append("s.measured_at >= ?")
        params.append(ensure_naive_utc(since))
    if until:
        where.append("s.measured_at < ?")
        params.append(ensure_naive_utc(until))

    sql = f"""
        SELECT
            s.score_id,
            s.step_id,
            s.track_id,
            s.student_id,
            s.metric_id,
            m.name AS metric_name,
            COALESCE(s.raw_value, s.value) AS value_raw,
            s.rater_user_id,
            s.role_at_rate,
            s.comment,
            s.measured_at AS occurred_at
        FROM scores s
        LEFT JOIN metrics m ON m.metric_id = s.metric_id
        WHERE {' AND '.join(where)}
        ORDER BY s.measured_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])

    with get_conn(True) as con:
        cur = con.execute(sql, params)
        return dictrows(cur)


def list_by_student(
    student_id: str,
    *,
    track_id: Optional[str] = None,
    metric_id: Optional[str] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    limit: int,
    offset: int,
) -> List[Dict[str, Any]]:
    where = ["s.student_id = ?"]
    params: List[Any] = [student_id]

    if track_id:
        where.append("s.track_id = ?")
        params.append(track_id)
    if metric_id:
        where.append("s.metric_id = ?")
        params.append(metric_id)
    if since:
        where.append("s.measured_at >= ?")
        params.append(ensure_naive_utc(since))
    if until:
        where.append("s.measured_at < ?")
        params.append(ensure_naive_utc(until))

    sql = f"""
        SELECT
            s.score_id,
            s.step_id,
            s.track_id,
            s.student_id,
            s.metric_id,
            m.name AS metric_name,
            COALESCE(s.raw_value, s.value) AS value_raw,
            s.rater_user_id,
            s.role_at_rate,
            s.comment,
            s.measured_at AS occurred_at
        FROM scores s
        LEFT JOIN metrics m ON m.metric_id = s.metric_id
        WHERE {' AND '.join(where)}
        ORDER BY s.measured_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])

    with get_conn(True) as con:
        cur = con.execute(sql, params)
        return dictrows(cur)


def list_by_sets(
    *,
    track_ids: Optional[List[str]] = None,
    student_ids: Optional[List[str]] = None,
    metric_ids: Optional[List[str]] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    limit: int,
    offset: int,
) -> List[Dict[str, Any]]:
    if track_ids is not None and len(track_ids) == 0:
        return []
    if student_ids is not None and len(student_ids) == 0:
        return []
    if metric_ids is not None and len(metric_ids) == 0:
        return []

    where: List[str] = []
    params: List[Any] = []

    if track_ids:
        placeholders = ", ".join(["?"] * len(track_ids))
        where.append(f"s.track_id IN ({placeholders})")
        params.extend(track_ids)
    if student_ids:
        placeholders = ", ".join(["?"] * len(student_ids))
        where.append(f"s.student_id IN ({placeholders})")
        params.extend(student_ids)
    if metric_ids:
        placeholders = ", ".join(["?"] * len(metric_ids))
        where.append(f"s.metric_id IN ({placeholders})")
        params.extend(metric_ids)
    if since:
        where.append("s.measured_at >= ?")
        params.append(ensure_naive_utc(since))
    if until:
        where.append("s.measured_at < ?")
        params.append(ensure_naive_utc(until))

    sql = """
        SELECT
            s.score_id,
            s.step_id,
            s.track_id,
            s.student_id,
            s.metric_id,
            m.name AS metric_name,
            COALESCE(s.raw_value, s.value) AS value_raw,
            s.rater_user_id,
            s.role_at_rate,
            s.comment,
            s.measured_at AS occurred_at
        FROM scores s
        LEFT JOIN metrics m ON m.metric_id = s.metric_id
    """

    if where:
        sql += " WHERE " + " AND ".join(where)

    sql += " ORDER BY s.measured_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with get_conn(True) as con:
        cur = con.execute(sql, params)
        return dictrows(cur)


def list_by_user(
    user_id: str,
    *,
    metric_id: Optional[str] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    limit: int,
    offset: int,
) -> List[Dict[str, Any]]:
    where = ["s.student_id = ?"]
    params: List[Any] = [user_id]

    if metric_id:
        where.append("s.metric_id = ?")
        params.append(metric_id)
    if since:
        where.append("s.measured_at >= ?")
        params.append(ensure_naive_utc(since))
    if until:
        where.append("s.measured_at < ?")
        params.append(ensure_naive_utc(until))

    sql = f"""
        SELECT
            s.score_id,
            s.step_id,
            s.track_id,
            s.student_id,
            s.metric_id,
            m.name AS metric_name,
            COALESCE(s.raw_value, s.value) AS value_raw,
            s.rater_user_id,
            s.role_at_rate,
            s.comment,
            s.measured_at AS occurred_at
        FROM scores s
        LEFT JOIN metrics m ON m.metric_id = s.metric_id
        WHERE {' AND '.join(where)}
        ORDER BY s.measured_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])

    with get_conn(True) as con:
        cur = con.execute(sql, params)
        return dictrows(cur)
