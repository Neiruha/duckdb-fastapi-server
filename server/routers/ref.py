from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..middleware.access import Caller, require_token
from ..schemas.reference import RefRequestIn, RefResponseOut
from ..services.reference_service import (
    get_message_types,
    get_metric_types,
    get_metrics,
    get_sys_event_types,
    get_track_step_types,
)

router = APIRouter(prefix="/ref", tags=["reference"])


@router.post("", response_model=RefResponseOut)
def ref_dispatch(
    payload: RefRequestIn,
    caller: Caller = Depends(require_token(allow_client=True)),  # noqa: ARG001
) -> RefResponseOut:
    if payload.op == "metrics.list":
        data = get_metrics()
    elif payload.op == "metric_types.list":
        data = get_metric_types()
    elif payload.op == "track_step_types.list":
        data = get_track_step_types()
    elif payload.op == "sys_event_types.list":
        data = get_sys_event_types()
    elif payload.op == "message_types.list":
        data = get_message_types()
    else:
        raise HTTPException(status_code=400, detail="Unknown op")

    return RefResponseOut(ok=True, op=payload.op, data=data)
