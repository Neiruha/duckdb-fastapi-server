from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class DBAliveOut(BaseModel):
    ok: bool = True
    backend: Literal["duckdb", "postgres"]
    generated_at: str
    last_sys_event_at: str | None = None
    last_system_message_at: str | None = None
    admin_direct_messages: int
    teacher_count: int
    student_count: int
    curator_count: int
    track_count: int
