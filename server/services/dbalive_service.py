from __future__ import annotations

from ..db import stats_repo
from ..schemas.dbalive import DBAliveOut
from ..utils.time import now_utc, to_warsaw_iso


def get_db_status() -> DBAliveOut:
    stats = stats_repo.fetch_db_health()
    last_event = stats.get("last_sys_event_at")
    last_event_iso = to_warsaw_iso(last_event) if last_event else None
    last_system_message = stats.get("last_system_message_at")
    last_system_message_iso = to_warsaw_iso(last_system_message) if last_system_message else None
    generated_at = to_warsaw_iso(now_utc())

    return DBAliveOut(
        ok=True,
        backend=stats["backend"],
        generated_at=generated_at,
        last_sys_event_at=last_event_iso,
        last_system_message_at=last_system_message_iso,
        admin_direct_messages=stats["admin_direct_messages"],
        teacher_count=stats["teacher_count"],
        student_count=stats["student_count"],
        curator_count=stats["curator_count"],
        track_count=stats["track_count"],
    )
