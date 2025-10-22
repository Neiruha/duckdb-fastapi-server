from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from fastapi import HTTPException

from ..config import (
    DEMO_MODE,
    SMOOTH_EMA_ALPHA,
    SMOOTH_GAP_STRATEGY,
    SMOOTH_SERIES_INTERVAL,
    SMOOTH_SERIES_MAX_POINTS,
    SMOOTH_WEIGHTS,
)
from ..db import scores_repo, tracks_repo
from ..middleware.access import Caller
from ..schemas.scores import ScoreOut, SmoothedSeriesOut, SmoothedSeriesPoint
from ..utils.time import ensure_naive_utc, now_utc


def get_scores_by_track(
    track_id: str,
    *,
    student_id: Optional[str] = None,
    metric_id: Optional[str] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    limit: int,
    offset: int,
) -> List[ScoreOut]:
    rows = scores_repo.list_by_track(
        track_id,
        student_id=student_id,
        metric_id=metric_id,
        since=since,
        until=until,
        limit=limit,
        offset=offset,
    )
    return [ScoreOut(**row) for row in rows]


def get_scores_by_student(
    student_id: str,
    *,
    track_id: Optional[str] = None,
    metric_id: Optional[str] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    limit: int,
    offset: int,
) -> List[ScoreOut]:
    rows = scores_repo.list_by_student(
        student_id,
        track_id=track_id,
        metric_id=metric_id,
        since=since,
        until=until,
        limit=limit,
        offset=offset,
    )
    return [ScoreOut(**row) for row in rows]


def get_scores_by_sets(
    *,
    track_ids: Optional[List[str]] = None,
    student_ids: Optional[List[str]] = None,
    metric_ids: Optional[List[str]] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    limit: int,
    offset: int,
) -> List[ScoreOut]:
    rows = scores_repo.list_by_sets(
        track_ids=track_ids,
        student_ids=student_ids,
        metric_ids=metric_ids,
        since=since,
        until=until,
        limit=limit,
        offset=offset,
    )
    return [ScoreOut(**row) for row in rows]


def _clamp(value: float) -> float:
    if value < 0:
        return 0.0
    if value > 100:
        return 100.0
    return value


def _align_start(dt: datetime, interval: str) -> datetime:
    aligned = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    if interval == "week":
        weekday = aligned.weekday()
        aligned -= timedelta(days=weekday)
    return aligned


def _build_interval_range(
    since: datetime,
    until: datetime,
    interval: str,
    max_points: int,
) -> List[datetime]:
    delta = timedelta(days=1) if interval == "day" else timedelta(weeks=1)
    start = _align_start(since, interval)
    end = _align_start(until, interval)
    if end < start:
        end = start
    current = start
    points: List[datetime] = []
    end_exclusive = end + delta
    while current < end_exclusive:
        points.append(current)
        current += delta
        if len(points) > max_points:
            raise HTTPException(status_code=400, detail="Requested interval exceeds max_points limit")
    return points


def _fill_gaps(values: List[Optional[float]]) -> List[float]:
    filled = [float(v) if v is not None else None for v in values]
    n = len(filled)
    idx = 0
    while idx < n:
        if filled[idx] is not None:
            filled[idx] = _clamp(float(filled[idx]))
            idx += 1
            continue
        start = idx
        while idx < n and filled[idx] is None:
            idx += 1
        end = idx  # exclusive
        prev_val = filled[start - 1] if start > 0 else None
        next_val = filled[idx] if idx < n else None
        gap_length = end - start
        if SMOOTH_GAP_STRATEGY == "linear" and prev_val is not None and next_val is not None:
            step = (next_val - prev_val) / (gap_length + 1)
            for offset in range(1, gap_length + 1):
                filled[start + offset - 1] = _clamp(prev_val + step * offset)
        elif prev_val is not None:
            for gap_idx in range(start, end):
                filled[gap_idx] = _clamp(prev_val)
        elif next_val is not None:
            for gap_idx in range(start, end):
                filled[gap_idx] = _clamp(next_val)
        else:
            for gap_idx in range(start, end):
                filled[gap_idx] = 0.0
    return [float(v) for v in filled]  # type: ignore[arg-type]


def _smooth(values: List[float]) -> List[float]:
    alpha = 0.5 if DEMO_MODE else SMOOTH_EMA_ALPHA
    smoothed: List[float] = []
    prev: Optional[float] = None
    for value in values:
        val = _clamp(value)
        if prev is None:
            prev = val
        else:
            prev = alpha * val + (1 - alpha) * prev
        smoothed.append(_clamp(prev))
    return smoothed


def _ensure_access(caller: Caller, track_id: str, student_id: Optional[str]) -> None:
    if caller.kind == "server":
        return
    if caller.kind != "client":
        raise HTTPException(status_code=403, detail="Forbidden")
    if student_id and caller.user_id == student_id:
        return
    if caller.user_id and tracks_repo.is_teacher(track_id, caller.user_id):
        return
    raise HTTPException(status_code=403, detail="Forbidden")


def get_smoothed_series(
    *,
    caller: Caller,
    track_id: str,
    student_id: Optional[str],
    metric_id: Optional[str],
    since: Optional[datetime],
    until: Optional[datetime],
    interval: Optional[str],
    max_points: Optional[int],
) -> SmoothedSeriesOut:
    _ensure_access(caller, track_id, student_id)

    interval_value = (interval or SMOOTH_SERIES_INTERVAL).lower()
    if interval_value not in {"day", "week"}:
        raise HTTPException(status_code=400, detail="Invalid interval")

    limit_points = max_points if max_points is not None else SMOOTH_SERIES_MAX_POINTS
    if limit_points <= 0:
        raise HTTPException(status_code=400, detail="max_points must be positive")
    if limit_points > SMOOTH_SERIES_MAX_POINTS:
        raise HTTPException(status_code=400, detail="max_points exceeds allowed maximum")

    track_window = tracks_repo.get_track_window(track_id)
    if not track_window:
        raise HTTPException(status_code=404, detail="Track not found")

    now = ensure_naive_utc(now_utc())
    start_at = track_window.get("start_at") or now
    end_at = track_window.get("end_at") or now

    since_dt = ensure_naive_utc(since) if since else ensure_naive_utc(start_at)
    until_dt = ensure_naive_utc(until) if until else ensure_naive_utc(end_at)

    if until_dt < since_dt:
        raise HTTPException(status_code=400, detail="until must be after since")

    points = _build_interval_range(since_dt, until_dt, interval_value, limit_points)
    if not points:
        points = [_align_start(since_dt, interval_value)]

    delta = timedelta(days=1) if interval_value == "day" else timedelta(weeks=1)

    sums: Dict[str, List[float]] = {"student": [0.0] * len(points), "teacher": [0.0] * len(points), "mentor": [0.0] * len(points)}
    counts: Dict[str, List[int]] = {"student": [0] * len(points), "teacher": [0] * len(points), "mentor": [0] * len(points)}

    series_rows = scores_repo.list_for_series(
        track_id,
        student_id=student_id,
        metric_id=metric_id,
        since=points[0],
        until=points[-1] + delta,
    )

    for row in series_rows:
        occurred_at = row.get("occurred_at")
        if occurred_at is None:
            continue
        dt = ensure_naive_utc(occurred_at)
        if dt < points[0] or dt >= points[-1] + delta:
            continue
        index = int((dt - points[0]) // delta)
        if not 0 <= index < len(points):
            continue
        role = (row.get("role_at_rate") or "").lower()
        if role not in sums:
            continue
        raw_value = row.get("value_raw")
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            continue
        sums[role][index] += value
        counts[role][index] += 1

    role_values: Dict[str, List[Optional[float]]] = {}
    for role, role_sums in sums.items():
        averages: List[Optional[float]] = []
        for idx, total in enumerate(role_sums):
            count = counts[role][idx]
            if count:
                averages.append(_clamp(total / count))
            else:
                averages.append(None)
        role_values[role] = averages

    student_series = _smooth(_fill_gaps(role_values["student"]))
    teacher_series = _smooth(_fill_gaps(role_values["teacher"]))
    mentor_series = _smooth(_fill_gaps(role_values["mentor"]))

    weights = SMOOTH_WEIGHTS
    points_out: List[SmoothedSeriesPoint] = []
    for idx, base in enumerate(points):
        student_val = student_series[idx]
        teacher_val = teacher_series[idx]
        mentor_val = mentor_series[idx]
        composite = (
            teacher_val * weights.get("teacher", 0)
            + mentor_val * weights.get("mentor", 0)
            + student_val * weights.get("student", 0)
        )
        points_out.append(
            SmoothedSeriesPoint(
                t=base.date().isoformat(),
                self_weighted=round(student_val, 2),
                teacher_weighted=round(teacher_val, 2),
                mentor_weighted=round(mentor_val, 2),
                composite=round(_clamp(composite), 2),
            )
        )

    return SmoothedSeriesOut(interval=interval_value, points=points_out)
