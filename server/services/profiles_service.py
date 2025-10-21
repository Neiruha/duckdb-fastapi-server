from __future__ import annotations

from ..db import flags_repo, sessions_repo, tracks_repo, users_repo
from ..schemas.profiles import ProfileByTelegramOut, ProfileUserOut
from ..schemas.tracks import TrackSummaryOut
from ..schemas.users import CuratorOut, TrackTeacherOut, TrackWithTeachersOut
from ..utils.time import now_utc, to_warsaw_iso


def profile_by_telegram(telegram_user_id: int) -> ProfileByTelegramOut:
    user = users_repo.get_by_telegram_id(telegram_user_id)
    if not user:
        return ProfileByTelegramOut()

    curator_raw = users_repo.get_curator(user.get("mentor_user_id"))
    curator = CuratorOut(**curator_raw) if curator_raw else None
    roles = users_repo.get_roles(user["user_id"])
    ban = flags_repo.get_ban_by_user(user["user_id"]) or flags_repo.get_ban_by_telegram(telegram_user_id)

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
        telegram_id=user.get("telegram_id"),
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
