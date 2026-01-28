from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ..middleware.access import Caller, need_server_role
from ..schemas.users import UserListOut
from ..services.users_service import list_by_role, list_users

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=UserListOut)
def user_list(
    caller: Caller = Depends(need_server_role),  # noqa: ARG001
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    role: str | None = Query(default=None),
) -> UserListOut:
    if role:
        return list_by_role(role, limit, offset)
    return list_users(limit, offset)
