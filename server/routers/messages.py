from __future__ import annotations

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, Query

from ..middleware.access import Caller, require_actor_caller, require_token
from ..schemas.messages import (
    MessageOut,
    MessageSendIn,
    MessageSendOut,
    MessagesMarkReadIn,
    MessagesMarkReadOut,
)
from ..services.messages_service import (
    list_inbox as service_list_inbox,
    list_sent as service_list_sent,
    mark_read as service_mark_read,
    send_message as service_send_message,
)

router = APIRouter(prefix="/messages", tags=["messages"])


@router.get("/my", response_model=List[MessageOut])
def my_messages(
    caller: Caller = Depends(require_token(allow_client=True, allow_server=False)),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    unread_only: bool = Query(default=False),
    since: datetime | None = Query(default=None),
    until: datetime | None = Query(default=None),
) -> List[MessageOut]:
    return service_list_inbox(
        caller=caller,
        limit=limit,
        offset=offset,
        unread_only=unread_only,
        since=since,
        until=until,
    )


@router.get("/sent", response_model=List[MessageOut])
def sent_messages(
    caller: Caller = Depends(require_token(allow_client=True, allow_server=False)),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    since: datetime | None = Query(default=None),
    until: datetime | None = Query(default=None),
) -> List[MessageOut]:
    return service_list_sent(
        caller=caller,
        limit=limit,
        offset=offset,
        since=since,
        until=until,
    )


@router.post("/send", response_model=MessageSendOut)
def send_message(
    payload: MessageSendIn,
    actor: tuple[Caller, str] = Depends(require_actor_caller),
) -> MessageSendOut:
    caller, actor_user_id = actor
    return service_send_message(caller=caller, actor_user_id=actor_user_id, payload=payload)


@router.post("/mark-read", response_model=MessagesMarkReadOut)
def mark_read(
    payload: MessagesMarkReadIn,
    actor: tuple[Caller, str] = Depends(require_actor_caller),
) -> MessagesMarkReadOut:
    caller, actor_user_id = actor
    return service_mark_read(caller=caller, actor_user_id=actor_user_id, payload=payload)
