from __future__ import annotations

from pydantic import BaseModel


class FlagsOut(BaseModel):
    exists: bool
    user_id: str | None = None
    frozen: bool | None = None
    banned: bool | None = None
