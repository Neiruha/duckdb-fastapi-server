from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class MetricOut(BaseModel):
    id: str
    name: str
    metric_type: str
    description: Optional[str] = None


class MetricTypeOut(BaseModel):
    id: str
    description: Optional[str] = None


class TrackStepTypeOut(BaseModel):
    id: str
    description: Optional[str] = None


class SysEventTypeOut(BaseModel):
    id: str
    description: Optional[str] = None


class MessageTypeOut(BaseModel):
    id: str
    description: Optional[str] = None
