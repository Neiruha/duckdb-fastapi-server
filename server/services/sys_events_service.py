from __future__ import annotations

from typing import Optional

from ..db import sys_events_repo


def write_sys_event(
    *,
    event_type: str,
    actor_user_id: Optional[str] = None,
    subject_user_id: Optional[str] = None,
    context: Optional[str] = None,
) -> str:
    return sys_events_repo.insert(
        event_type=event_type,
        actor_user_id=actor_user_id,
        subject_user_id=subject_user_id,
        context=context,
    )
