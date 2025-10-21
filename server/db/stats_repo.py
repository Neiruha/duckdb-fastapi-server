from __future__ import annotations

from typing import Any, Dict

from .connection import get_conn
from ..config import DB_BACKEND
from ..logging_utils import get_logger

log = get_logger("db.stats")


def fetch_db_health() -> Dict[str, Any]:
    """Return connectivity confirmation and aggregated statistics."""
    with get_conn(True) as con:
        # Connectivity check
        con.execute("SELECT 1").fetchone()

        last_sys_event = con.execute(
            "SELECT MAX(occurred_at) FROM sys_events"
        ).fetchone()[0]

        last_system_message = con.execute(
            "SELECT MAX(created_at) FROM messages WHERE message_type = 'system'"
        ).fetchone()[0]

        admin_dm_count = con.execute(
            """
            SELECT COUNT(*)
            FROM message_recipients mr
            JOIN user_roles ur ON mr.recipient_user_id = ur.user_id
            WHERE ur.role = 'admin'
            """
        ).fetchone()[0]

        teacher_count = con.execute(
            "SELECT COUNT(DISTINCT user_id) FROM user_roles WHERE role = 'teacher'"
        ).fetchone()[0]

        student_count = con.execute(
            "SELECT COUNT(DISTINCT user_id) FROM user_roles WHERE role = 'student'"
        ).fetchone()[0]

        curator_count = con.execute(
            "SELECT COUNT(DISTINCT user_id) FROM user_roles WHERE role = 'mentor'"
        ).fetchone()[0]

        track_count = con.execute("SELECT COUNT(*) FROM tracks").fetchone()[0]

    return {
        "backend": DB_BACKEND,
        "last_sys_event_at": last_sys_event,
        "last_system_message_at": last_system_message,
        "admin_direct_messages": int(admin_dm_count or 0),
        "teacher_count": int(teacher_count or 0),
        "student_count": int(student_count or 0),
        "curator_count": int(curator_count or 0),
        "track_count": int(track_count or 0),
    }
