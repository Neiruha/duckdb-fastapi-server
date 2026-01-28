from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends

from ..middleware.access import Caller, require_token
from ..schemas.scores import ScoreOut, ScoresQueryIn
from ..services.scores_service import get_scores_by_sets

router = APIRouter(prefix="/scores", tags=["scores"])

@router.post("/query", response_model=List[ScoreOut])
def scores_query(
    payload: ScoresQueryIn,
    caller: Caller = Depends(require_token(allow_client=True)),  # noqa: ARG001
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
