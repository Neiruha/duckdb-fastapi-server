from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel


class MetricOut(BaseModel):
    id: str
    name: str
    kind: str
    system: Optional[str] = None
    code: Optional[str] = None
    members: Optional[object] = None
    description: Optional[str] = None


class MetricTypeOut(BaseModel):
    id: str


class TrackStepTypeOut(BaseModel):
    id: str
    description: Optional[str] = None


class SysEventTypeOut(BaseModel):
    id: str
    description: Optional[str] = None


class MessageTypeOut(BaseModel):
    id: str
    description: Optional[str] = None


class RefRequestIn(BaseModel):
    op: str
    params: dict[str, Any] | None = None


class RefResponseOut(BaseModel):
    ok: bool
    op: str
    data: Any
