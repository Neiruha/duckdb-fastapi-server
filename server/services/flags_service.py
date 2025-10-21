from __future__ import annotations

from ..db import flags_repo, users_repo
from ..schemas.flags import FlagsOut


def flags_by_telegram(telegram_user_id: int) -> FlagsOut:
    user = users_repo.get_by_telegram_id(telegram_user_id)
    if not user:
        ban = flags_repo.get_ban_by_telegram(telegram_user_id)
        if ban:
            return FlagsOut(exists=False, banned=True)
        return FlagsOut(exists=False)

    ban = flags_repo.get_ban_by_user(user["user_id"]) or flags_repo.get_ban_by_telegram(telegram_user_id)
    return FlagsOut(
        exists=True,
        user_id=user["user_id"],
        frozen=bool(user.get("frozen")),
        banned=ban is not None,
    )
