from __future__ import annotations

from typing import Any, Dict, List

from fastapi import HTTPException

from ..db import flags_repo, sessions_repo, tracks_repo, users_repo
from ..schemas.profiles import (
    ProfileByTelegramOut,
    ProfileHeaderOut,
    ProfileResponseOut,
    ProfileTrackOut,
    ProfileType,
    ProfileUserOut,
)
from ..schemas.tracks import TrackSummaryOut
from ..schemas.users import CuratorOut, TrackTeacherOut, TrackWithTeachersOut
from ..utils.time import now_utc, to_warsaw_iso


def _build_profile(user: Dict[str, Any]) -> ProfileByTelegramOut:
    curator_raw = users_repo.get_curator(user.get("mentor_user_id"))
    curator = CuratorOut(**curator_raw) if curator_raw else None
    roles = users_repo.get_roles(user["user_id"])

    ban = flags_repo.get_ban_by_user(user["user_id"])
    telegram_id = user.get("telegram_id")
    if ban is None and telegram_id is not None:
        ban = flags_repo.get_ban_by_telegram(telegram_id)

    now = now_utc()
    tracks_student_raw = tracks_repo.list_by_student(user["user_id"], active_only=True, now=now)
    tracks_student = []
    for track in tracks_student_raw:
        teachers_raw = tracks_repo.list_teachers_for_track(track["track_id"])
        teachers = [TrackTeacherOut(**teacher) for teacher in teachers_raw]
        tracks_student.append(
            TrackWithTeachersOut(
                track_id=track["track_id"],
                title=track["title"],
                status=track["status"],
                teachers=teachers,
            )
        )

    tracks_teacher_raw = tracks_repo.list_by_teacher(user["user_id"], active_only=True, now=now)
    tracks_teacher = [TrackSummaryOut(**track) for track in tracks_teacher_raw]

    last_seen = sessions_repo.last_seen_at(user["user_id"])
    last_seen_iso = to_warsaw_iso(last_seen) if last_seen else None

    profile_user = ProfileUserOut(
        user_id=user["user_id"],
        display_name=user["display_name"],
        telegram_id=telegram_id,
        telegram_username=user.get("telegram_username"),
        telegram_login_name=user.get("telegram_login_name"),
        frozen=bool(user.get("frozen")),
        banned=ban is not None,
        roles=roles,
        mentor_user_id=user.get("mentor_user_id"),
        curator=curator,
    )

    return ProfileByTelegramOut(
        user=profile_user,
        tracks_active_as_student=tracks_student,
        tracks_active_as_teacher=tracks_teacher,
        last_seen_at=last_seen_iso,
    )


def profile_by_telegram(telegram_user_id: int) -> ProfileByTelegramOut:
    user = users_repo.get_by_telegram_id(telegram_user_id)
    if not user:
        return ProfileByTelegramOut()
    return _build_profile(user)


def profile_by_user_type(user_id: str, profile_type: ProfileType) -> ProfileResponseOut:
    if profile_type in {"charts", "disc_profile"}:
        raise HTTPException(status_code=501, detail=f"Profile type '{profile_type}' is planned but not implemented yet.")

    user = users_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    curator_raw = users_repo.get_curator(user.get("mentor_user_id"))
    curator = CuratorOut(**curator_raw) if curator_raw else None
    roles = users_repo.get_roles(user["user_id"])

    ban = flags_repo.get_ban_by_user(user["user_id"])
    telegram_id = user.get("telegram_id")
    if ban is None and telegram_id is not None:
        ban = flags_repo.get_ban_by_telegram(telegram_id)

    header = ProfileHeaderOut(
        user_id=user["user_id"],
        display_name=user["display_name"],
        telegram_id=telegram_id,
        telegram_username=user.get("telegram_username"),
        telegram_login_name=user.get("telegram_login_name"),
        telegram_photo_url=user.get("telegram_photo_url"),
        frozen=bool(user.get("frozen")),
        banned=ban is not None,
        roles=roles,
        mentor_user_id=user.get("mentor_user_id"),
        curator=curator,
    )

    tracks: List[ProfileTrackOut] = []
    if profile_type in {"tracks", "full"}:
        track_rows = tracks_repo.list_tracks_for_user(user_id)
        for row in track_rows:
            joined_at = row.get("joined_at")
            joined_at_iso = to_warsaw_iso(joined_at) if joined_at else None
            tracks.append(
                ProfileTrackOut(
                    track_id=row["track_id"],
                    title=row["title"],
                    status=row["status"],
                    owner_user_id=row["owner_user_id"],
                    role_in_track=row["role_in_track"],
                    joined_at=joined_at_iso,
                )
            )

    if profile_type == "header":
        return ProfileResponseOut(profile_type=profile_type, header=header)
    if profile_type == "tracks":
        return ProfileResponseOut(profile_type=profile_type, tracks=tracks)
    return ProfileResponseOut(profile_type=profile_type, header=header, tracks=tracks)
