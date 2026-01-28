from __future__ import annotations

from ..db import users_repo
from ..schemas.users import UserListItem, UserListOut
from ..utils.time import to_warsaw_iso


def list_users(limit: int, offset: int) -> UserListOut:
    data = users_repo.list_users(limit, offset)
    items = []
    for item in data["items"]:
        last_seen = item.get("last_seen_at")
        last_seen_iso = to_warsaw_iso(last_seen) if last_seen else None
        items.append(
            UserListItem(
                user_id=item["user_id"],
                display_name=item["display_name"],
                telegram_id=item.get("telegram_id"),
                telegram_username=item.get("telegram_username"),
                web_login=item.get("web_login"),
                last_seen_at=last_seen_iso,
            )
        )
    return UserListOut(total=data["total"], items=items)


def list_by_role(role: str, limit: int, offset: int) -> UserListOut:
    data = users_repo.list_users_by_role(role, limit, offset)
    items = []
    for item in data["items"]:
        last_seen = item.get("last_seen_at")
        last_seen_iso = to_warsaw_iso(last_seen) if last_seen else None
        items.append(
            UserListItem(
                user_id=item["user_id"],
                display_name=item["display_name"],
                telegram_id=item.get("telegram_id"),
                telegram_username=item.get("telegram_username"),
                web_login=item.get("web_login"),
                last_seen_at=last_seen_iso,
            )
        )
    return UserListOut(total=data["total"], items=items)
