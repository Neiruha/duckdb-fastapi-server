from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ScoreOut(BaseModel):
    score_id: str
    step_id: str | None = None
    track_id: str
    student_id: str
    metric_id: str
    metric_name: Optional[str] = None
    value_raw: float
    value_smooth: float
    rater_user_id: str
    role_at_rate: Optional[str] = None
    comment: Optional[str] = None
    occurred_at: datetime


class ScoresQueryIn(BaseModel):
    track_ids: Optional[List[str]] = None
    student_ids: Optional[List[str]] = None
    metric_ids: Optional[List[str]] = None
    since: Optional[datetime] = None
    until: Optional[datetime] = None
    limit: int = Field(200, ge=1, le=2000)
    offset: int = Field(0, ge=0)
