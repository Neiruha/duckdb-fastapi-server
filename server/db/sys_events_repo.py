from __future__ import annotations

from typing import Optional

from .connection import get_conn
from ..logging_utils import get_logger
from ..utils.ids import new_id

log = get_logger("db.sys_events")


def insert(
    *,
    event_type: str,
    actor_user_id: Optional[str],
    subject_user_id: Optional[str],
    context: Optional[str],
) -> str:
    sys_event_id = new_id("se_")
    with get_conn(False) as con:
        con.execute(
            """
            INSERT INTO sys_events (sys_event_id, event_type, actor_user_id, subject_user_id, context)
            VALUES (?, ?, ?, ?, ?)
            """,
            [sys_event_id, event_type, actor_user_id, subject_user_id, context],
        )
    log.info(
        "Inserted sys_event %s type=%s subject=%s", sys_event_id, event_type, subject_user_id
    )
    return sys_event_id
