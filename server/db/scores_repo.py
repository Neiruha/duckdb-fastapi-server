from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from .connection import dictrows, get_conn
from ..utils.time import ensure_naive_utc


def _clamp_score(value: Any) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0.0
    if numeric < 0:
        return 0.0
    if numeric > 100:
        return 100.0
    return numeric


def _with_smoothing(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    for row in rows:
        raw_value = row.get("value_raw")
        row["value_raw"] = float(raw_value) if raw_value is not None else 0.0
        row["value_smooth"] = _clamp_score(raw_value)
    return rows


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
    where = ["ts.track_id = ?"]
    params: List[Any] = [track_id]

    if student_id:
        where.append("sms.student_id = ?")
        params.append(student_id)
    if metric_id:
        where.append("sms.metric_id = ?")
        params.append(metric_id)
    if since:
        where.append("ts.occurred_at >= ?")
        params.append(ensure_naive_utc(since))
    if until:
        where.append("ts.occurred_at < ?")
        params.append(ensure_naive_utc(until))

    sql = f"""
        SELECT
            sms.score_id,
            sms.step_id,
            ts.track_id,
            sms.student_id,
            sms.metric_id,
            m.name AS metric_name,
            sms.value AS value_raw,
            sms.rater_user_id,
            sms.role_at_rate,
            sms.comment,
            ts.occurred_at
        FROM step_metric_scores sms
        JOIN track_steps ts ON ts.step_id = sms.step_id
        LEFT JOIN metrics m ON m.metric_id = sms.metric_id
        WHERE {' AND '.join(where)}
        ORDER BY ts.occurred_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])

    with get_conn(True) as con:
        cur = con.execute(sql, params)
        return _with_smoothing(dictrows(cur))


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
    where = ["sms.student_id = ?"]
    params: List[Any] = [student_id]

    if track_id:
        where.append("ts.track_id = ?")
        params.append(track_id)
    if metric_id:
        where.append("sms.metric_id = ?")
        params.append(metric_id)
    if since:
        where.append("ts.occurred_at >= ?")
        params.append(ensure_naive_utc(since))
    if until:
        where.append("ts.occurred_at < ?")
        params.append(ensure_naive_utc(until))

    sql = f"""
        SELECT
            sms.score_id,
            sms.step_id,
            ts.track_id,
            sms.student_id,
            sms.metric_id,
            m.name AS metric_name,
            sms.value AS value_raw,
            sms.rater_user_id,
            sms.role_at_rate,
            sms.comment,
            ts.occurred_at
        FROM step_metric_scores sms
        JOIN track_steps ts ON ts.step_id = sms.step_id
        LEFT JOIN metrics m ON m.metric_id = sms.metric_id
        WHERE {' AND '.join(where)}
        ORDER BY ts.occurred_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])

    with get_conn(True) as con:
        cur = con.execute(sql, params)
        return _with_smoothing(dictrows(cur))


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
        where.append(f"ts.track_id IN ({placeholders})")
        params.extend(track_ids)
    if student_ids:
        placeholders = ", ".join(["?"] * len(student_ids))
        where.append(f"sms.student_id IN ({placeholders})")
        params.extend(student_ids)
    if metric_ids:
        placeholders = ", ".join(["?"] * len(metric_ids))
        where.append(f"sms.metric_id IN ({placeholders})")
        params.extend(metric_ids)
    if since:
        where.append("ts.occurred_at >= ?")
        params.append(ensure_naive_utc(since))
    if until:
        where.append("ts.occurred_at < ?")
        params.append(ensure_naive_utc(until))

    sql = """
        SELECT
            sms.score_id,
            sms.step_id,
            ts.track_id,
            sms.student_id,
            sms.metric_id,
            m.name AS metric_name,
            sms.value AS value_raw,
            sms.rater_user_id,
            sms.role_at_rate,
            sms.comment,
            ts.occurred_at
        FROM step_metric_scores sms
        JOIN track_steps ts ON ts.step_id = sms.step_id
        LEFT JOIN metrics m ON m.metric_id = sms.metric_id
    """

    if where:
        sql += " WHERE " + " AND ".join(where)

    sql += " ORDER BY ts.occurred_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with get_conn(True) as con:
        cur = con.execute(sql, params)
        return _with_smoothing(dictrows(cur))


def list_for_series(
    track_id: str,
    *,
    student_id: Optional[str] = None,
    metric_id: Optional[str] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    where = ["ts.track_id = ?"]
    params: List[Any] = [track_id]

    if student_id:
        where.append("sms.student_id = ?")
        params.append(student_id)
    if metric_id:
        where.append("sms.metric_id = ?")
        params.append(metric_id)
    if since:
        where.append("ts.occurred_at >= ?")
        params.append(ensure_naive_utc(since))
    if until:
        where.append("ts.occurred_at < ?")
        params.append(ensure_naive_utc(until))

    sql = f"""
        SELECT
            ts.occurred_at,
            sms.value AS value_raw,
            sms.role_at_rate,
            sms.metric_id,
            sms.student_id
        FROM step_metric_scores sms
        JOIN track_steps ts ON ts.step_id = sms.step_id
        WHERE {' AND '.join(where)}
        ORDER BY ts.occurred_at ASC
    """

    with get_conn(True) as con:
        cur = con.execute(sql, params)
        return dictrows(cur)
