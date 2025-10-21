from __future__ import annotations

from fastapi import APIRouter, Depends

from ..middleware.access import require_token
from ..schemas.profiles import ProfileByTelegramOut
from ..services.profiles_service import profile_by_telegram

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("/by-telegram/{telegram_user_id}", response_model=ProfileByTelegramOut)
def profile_by_telegram_route(
    telegram_user_id: int,
    role: str = Depends(require_token()),  # noqa: ARG001
) -> ProfileByTelegramOut:
    return profile_by_telegram(telegram_user_id)
