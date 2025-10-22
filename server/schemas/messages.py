from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class MessageOut(BaseModel):
    message_id: str
    message_type: Optional[str] = None
    content: Optional[str] = None
    message_data_json: Optional[Dict[str, Any]] = None
    sender_user_id: Optional[str] = None
    recipient_user_id: Optional[str] = None
    created_at: datetime
    read_flag: Optional[bool] = None


class MessageSendIn(BaseModel):
    to_telegram_user_id: int = Field(..., gt=0)
    message_type: Optional[str] = Field(default="text")
    content: str
    data: Optional[Dict[str, Any]] = None


class MessageSendOut(BaseModel):
    message_id: str
    recipient_user_id: str


class MessagesMarkReadIn(BaseModel):
    message_ids: List[str]

    @validator("message_ids")
    def _non_empty(cls, value: List[str]) -> List[str]:
        if not value:
            raise ValueError("message_ids must not be empty")
        return value


class MessagesMarkReadOut(BaseModel):
    updated: int
