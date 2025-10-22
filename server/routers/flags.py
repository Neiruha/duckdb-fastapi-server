from __future__ import annotations

from fastapi import APIRouter, Depends

from ..middleware.access import Caller, require_token
from ..schemas.flags import FlagsOut
from ..services.flags_service import flags_by_telegram

router = APIRouter(prefix="/flags", tags=["flags"])


@router.get("/telegram/{telegram_user_id}", response_model=FlagsOut)
def flags_telegram(telegram_user_id: int, caller: Caller = Depends(require_token())) -> FlagsOut:  # noqa: ARG001
    return flags_by_telegram(telegram_user_id)
