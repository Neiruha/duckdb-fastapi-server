from __future__ import annotations

from fastapi import APIRouter, Depends

from ..middleware.access import Caller, require_token
from ..schemas.profiles import ProfileByTelegramOut
from ..services.profiles_service import profile_by_telegram, profile_by_user_id

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("/by-telegram/{telegram_user_id}", response_model=ProfileByTelegramOut)
def profile_by_telegram_route(
    telegram_user_id: int,
    caller: Caller = Depends(require_token(allow_client=True)),  # noqa: ARG001
) -> ProfileByTelegramOut:
    return profile_by_telegram(telegram_user_id)


@router.get("/by-user/{user_id}", response_model=ProfileByTelegramOut)
def profile_by_user_route(
    user_id: str,
    caller: Caller = Depends(require_token(allow_client=True)),  # noqa: ARG001
) -> ProfileByTelegramOut:
    return profile_by_user_id(user_id)
