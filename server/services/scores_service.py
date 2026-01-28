from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from ..db import scores_repo
from ..schemas.scores import ScoreOut


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


