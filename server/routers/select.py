from __future__ import annotations

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..db import sandbox
from ..middleware.access import Caller, need_server_role

router = APIRouter(prefix="/select", tags=["select"])


class SelectQueryIn(BaseModel):
    sql: str
    params: List[Any] = Field(default_factory=list)


class SelectQueryOut(BaseModel):
    columns: List[str]
    rows: List[List[Any]]


@router.post("", response_model=SelectQueryOut)
def run_select(
    payload: SelectQueryIn,
    caller: Caller = Depends(need_server_role),
) -> SelectQueryOut:
    del caller
    try:
        columns, rows = sandbox.select(payload.sql, payload.params)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    return SelectQueryOut(columns=columns, rows=rows)
