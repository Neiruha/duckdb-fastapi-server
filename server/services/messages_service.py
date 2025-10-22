from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status

from ..db import messages_repo, users_repo
from ..middleware.access import Caller
from ..schemas.messages import (
    MessageOut,
    MessageSendIn,
    MessageSendOut,
    MessagesMarkReadIn,
    MessagesMarkReadOut,
)
from .sys_events_service import write_sys_event


def _normalize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    message_data = row.get("message_data_json")
    if isinstance(message_data, str):
        try:
            message_data = json.loads(message_data)
        except json.JSONDecodeError:
            message_data = None
    elif message_data is None:
        message_data = None

    normalized = dict(row)
    normalized["message_data_json"] = message_data
    read_flag = normalized.get("read_flag")
    if read_flag is not None:
        normalized["read_flag"] = bool(read_flag)
    return normalized


def list_inbox(
    *,
    caller: Caller,
    limit: int,
    offset: int,
    unread_only: bool,
    since: Optional[datetime],
    until: Optional[datetime],
) -> List[MessageOut]:
    if caller.kind != "client" or not caller.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Client token required")

    rows = messages_repo.list_inbox(
        recipient_user_id=caller.user_id,
        limit=limit,
        offset=offset,
        unread_only=unread_only,
        since=since,
        until=until,
    )
    return [MessageOut(**_normalize_row(row)) for row in rows]


def list_sent(
    *,
    caller: Caller,
    limit: int,
    offset: int,
    since: Optional[datetime],
    until: Optional[datetime],
) -> List[MessageOut]:
    if caller.kind != "client" or not caller.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Client token required")

    rows = messages_repo.list_sent(
        sender_user_id=caller.user_id,
        limit=limit,
        offset=offset,
        since=since,
        until=until,
    )
    return [MessageOut(**_normalize_row(row)) for row in rows]


def send_message(*, caller: Caller, payload: MessageSendIn) -> MessageSendOut:
    message_type = payload.message_type or "text"
    recipient = users_repo.get_by_telegram_id(payload.to_telegram_user_id)
    if not recipient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipient not found")

    sender_user_id: Optional[str] = None
    if caller.kind == "client":
        if not caller.user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Client token required")
        sender_user_id = caller.user_id
    elif caller.kind == "server":
        sender_user_id = caller.user_id
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unsupported token")

    inserted = messages_repo.insert_message(
        sender_user_id=sender_user_id,
        recipient_user_id=recipient["user_id"],
        recipient_telegram_user_id=recipient.get("telegram_id"),
        message_type=message_type,
        content=payload.content,
        message_data=payload.data,
    )

    write_sys_event(
        event_type="message_sent",
        actor_user_id=sender_user_id,
        subject_user_id=recipient["user_id"],
        context="messages/send",
    )

    return MessageSendOut(**inserted)


def mark_read(*, caller: Caller, payload: MessagesMarkReadIn) -> MessagesMarkReadOut:
    if caller.kind == "client":
        if not caller.user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Client token required")
        updated = messages_repo.mark_read(
            message_ids=payload.message_ids,
            recipient_user_id=caller.user_id,
        )
        if updated:
            write_sys_event(
                event_type="message_read",
                actor_user_id=caller.user_id,
                subject_user_id=caller.user_id,
                context="messages/mark-read",
            )
        return MessagesMarkReadOut(updated=updated)

    if caller.kind == "server":
        updated = messages_repo.mark_read(message_ids=payload.message_ids, recipient_user_id=None)
        if updated:
            write_sys_event(
                event_type="message_read",
                actor_user_id=None,
                subject_user_id=None,
                context="messages/mark-read/server",
            )
        return MessagesMarkReadOut(updated=updated)

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unsupported token")
