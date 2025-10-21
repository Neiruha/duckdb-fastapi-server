from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from ..middleware.access import need_server_role, require_token
from ..schemas.users import GetUserInfoIn, UserInfoOut, UserListOut
from ..services.users_service import get_user_info, list_users

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/info", response_model=UserInfoOut)
def user_info(payload: GetUserInfoIn, role: str = Depends(require_token())) -> UserInfoOut:  # noqa: ARG001
    if not any([payload.user_id, payload.telegram_user_id, payload.telegram_user_name]):
        raise HTTPException(status_code=400, detail="Provide one of: user_id | telegram_user_id | telegram_user_name")
    data = get_user_info(
        user_id=payload.user_id,
        telegram_user_id=payload.telegram_user_id,
        telegram_user_name=payload.telegram_user_name,
    )
    if not data:
        raise HTTPException(status_code=404, detail="User not found")
    return data


@router.get("", response_model=UserListOut)
def user_list(
    role: str = Depends(need_server_role),  # noqa: ARG001
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> UserListOut:
    return list_users(limit, offset)
