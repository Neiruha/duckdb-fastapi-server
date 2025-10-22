from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends

from ..middleware.access import Caller, require_token
from ..schemas.reference import (
    MessageTypeOut,
    MetricOut,
    MetricTypeOut,
    SysEventTypeOut,
    TrackStepTypeOut,
)
from ..services.reference_service import (
    get_message_types,
    get_metric_types,
    get_metrics,
    get_sys_event_types,
    get_track_step_types,
)

router = APIRouter(tags=["reference"])


@router.get("/metrics", response_model=List[MetricOut])
def metrics_list(caller: Caller = Depends(require_token(allow_client=True))) -> List[MetricOut]:  # noqa: ARG001
    return get_metrics()


@router.get("/metric-types", response_model=List[MetricTypeOut])
def metric_types_list(caller: Caller = Depends(require_token(allow_client=True))) -> List[MetricTypeOut]:  # noqa: ARG001
    return get_metric_types()


@router.get("/track-step-types", response_model=List[TrackStepTypeOut])
def track_step_types_list(caller: Caller = Depends(require_token(allow_client=True))) -> List[TrackStepTypeOut]:  # noqa: ARG001
    return get_track_step_types()


@router.get("/sys-event-types", response_model=List[SysEventTypeOut])
def sys_event_types_list(caller: Caller = Depends(require_token(allow_client=True))) -> List[SysEventTypeOut]:  # noqa: ARG001
    return get_sys_event_types()


@router.get("/message-types", response_model=List[MessageTypeOut])
def message_types_list(caller: Caller = Depends(require_token(allow_client=True))) -> List[MessageTypeOut]:  # noqa: ARG001
    return get_message_types()
