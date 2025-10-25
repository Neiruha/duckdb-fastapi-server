from __future__ import annotations

from typing import Optional

from ..db import tracks_repo, users_repo
from ..schemas.users import (
    CuratorOut,
    TrackTeacherOut,
    TrackWithTeachersOut,
    UserInfoOut,
    UserListItem,
    UserListOut,
    UserRenamedOut,
)
from ..utils.time import now_utc, to_warsaw_iso


def get_user_info(
    *,
    user_id: Optional[str],
    telegram_user_id: Optional[int],
    telegram_user_name: Optional[str],
) -> Optional[UserInfoOut]:
    user = users_repo.find_user(user_id, telegram_user_id, telegram_user_name)
    if not user:
        return None

    curator_raw = users_repo.get_curator(user.get("mentor_user_id"))
    curator = CuratorOut(**curator_raw) if curator_raw else CuratorOut()
    roles = users_repo.get_roles(user["user_id"])

    now = now_utc()
    tracks_raw = tracks_repo.list_by_student(user["user_id"], active_only=True, now=now)
    tracks = []
    for track in tracks_raw:
        teachers_raw = tracks_repo.list_teachers_for_track(track["track_id"])
        teachers = [TrackTeacherOut(**teacher) for teacher in teachers_raw]
        tracks.append(
            TrackWithTeachersOut(
                track_id=track["track_id"],
                title=track["title"],
                status=track["status"],
                teachers=teachers,
            )
        )

    return UserInfoOut(
        user_id=user["user_id"],
        display_name=user["display_name"],
        telegram_id=user.get("telegram_id"),
        telegram_username=user.get("telegram_username"),
        telegram_login_name=user.get("telegram_login_name"),
        curator=curator,
        roles=roles,
        active_tracks=tracks,
    )


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


def rename_user(user_id: str, display_name: str) -> UserRenamedOut | None:
    row = users_repo.rename_display_name(user_id, display_name)
    if not row:
        return None
    return UserRenamedOut(**row)
