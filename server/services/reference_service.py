from __future__ import annotations

from typing import List

from ..db import reference_repo
from ..schemas.reference import (
    MetricOut,
    MetricTypeOut,
    MessageTypeOut,
    TrackStepTypeOut,
    SysEventTypeOut,
)


def get_metrics() -> List[MetricOut]:
    rows = reference_repo.list_metrics()
    return [MetricOut(**row) for row in rows]


def get_metric_types() -> List[MetricTypeOut]:
    rows = reference_repo.list_metric_types()
    return [MetricTypeOut(**row) for row in rows]


def get_track_step_types() -> List[TrackStepTypeOut]:
    rows = reference_repo.list_track_step_types()
    return [TrackStepTypeOut(**row) for row in rows]


def get_sys_event_types() -> List[SysEventTypeOut]:
    rows = reference_repo.list_sys_event_types()
    return [SysEventTypeOut(**row) for row in rows]


def get_message_types() -> List[MessageTypeOut]:
    rows = reference_repo.list_message_types()
    return [MessageTypeOut(**row) for row in rows]
