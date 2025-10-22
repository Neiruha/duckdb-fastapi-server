from __future__ import annotations

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, Query

from ..middleware.access import Caller, require_token
from ..schemas.scores import ScoreOut, ScoresQueryIn, SmoothedSeriesOut
from ..services.scores_service import (
    get_scores_by_sets,
    get_scores_by_student,
    get_scores_by_track,
    get_smoothed_series,
)

router = APIRouter(prefix="/scores", tags=["scores"])


@router.get("/track/{track_id}", response_model=List[ScoreOut])
def scores_by_track(
    track_id: str,
    caller: Caller = Depends(require_token()),  # noqa: ARG001
    student_id: str | None = Query(default=None),
    metric_id: str | None = Query(default=None),
    since: datetime | None = Query(default=None),
    until: datetime | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=2000),
    offset: int = Query(default=0, ge=0),
) -> List[ScoreOut]:
    return get_scores_by_track(
        track_id,
        student_id=student_id,
        metric_id=metric_id,
        since=since,
        until=until,
        limit=limit,
        offset=offset,
    )


@router.get("/student/{student_id}", response_model=List[ScoreOut])
def scores_by_student(
    student_id: str,
    caller: Caller = Depends(require_token()),  # noqa: ARG001
    track_id: str | None = Query(default=None),
    metric_id: str | None = Query(default=None),
    since: datetime | None = Query(default=None),
    until: datetime | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=2000),
    offset: int = Query(default=0, ge=0),
) -> List[ScoreOut]:
    return get_scores_by_student(
        student_id,
        track_id=track_id,
        metric_id=metric_id,
        since=since,
        until=until,
        limit=limit,
        offset=offset,
    )


@router.post("/query", response_model=List[ScoreOut])
def scores_query(
    payload: ScoresQueryIn,
    caller: Caller = Depends(require_token()),  # noqa: ARG001
) -> List[ScoreOut]:
    return get_scores_by_sets(
        track_ids=payload.track_ids,
        student_ids=payload.student_ids,
        metric_ids=payload.metric_ids,
        since=payload.since,
        until=payload.until,
        limit=payload.limit,
        offset=payload.offset,
    )


@router.get("/smoothed-series", response_model=SmoothedSeriesOut)
def smoothed_series(
    track_id: str = Query(...),
    caller: Caller = Depends(require_token(allow_client=True)),
    student_id: str | None = Query(default=None),
    metric_id: str | None = Query(default=None),
    interval: str | None = Query(default=None),
    max_points: int | None = Query(default=None, ge=1, le=2000),
    since: datetime | None = Query(default=None),
    until: datetime | None = Query(default=None),
) -> SmoothedSeriesOut:
    return get_smoothed_series(
        caller=caller,
        track_id=track_id,
        student_id=student_id,
        metric_id=metric_id,
        since=since,
        until=until,
        interval=interval,
        max_points=max_points,
    )
