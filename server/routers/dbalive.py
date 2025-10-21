from __future__ import annotations

from fastapi import APIRouter, Depends

from ..middleware.access import need_server_role
from ..schemas.dbalive import DBAliveOut
from ..services.dbalive_service import get_db_status

router = APIRouter(prefix="/dbalive", tags=["db"])


@router.get("", response_model=DBAliveOut)
def dbalive(role: str = Depends(need_server_role)) -> DBAliveOut:  # noqa: ARG001
    return get_db_status()
