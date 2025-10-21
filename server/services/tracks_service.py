from __future__ import annotations

from ..db import tracks_repo
from ..schemas.tracks import TrackRenamedOut, TrackSummaryOut
from ..schemas.users import TrackTeacherOut, TrackWithTeachersOut
from ..utils.time import now_utc


def tracks_for_teacher(user_id: str, active_only: bool) -> list[TrackSummaryOut]:
    rows = tracks_repo.list_by_teacher(user_id, active_only=active_only, now=now_utc())
    return [TrackSummaryOut(**row) for row in rows]


def tracks_for_student(user_id: str, active_only: bool) -> list[TrackWithTeachersOut]:
    rows = tracks_repo.list_by_student(user_id, active_only=active_only, now=now_utc())
    result: list[TrackWithTeachersOut] = []
    for row in rows:
        teachers_raw = tracks_repo.list_teachers_for_track(row["track_id"])
        teachers = [TrackTeacherOut(**teacher) for teacher in teachers_raw]
        result.append(
            TrackWithTeachersOut(
                track_id=row["track_id"],
                title=row["title"],
                status=row["status"],
                teachers=teachers,
            )
        )
    return result


def tracks_all_active() -> list[TrackSummaryOut]:
    rows = tracks_repo.list_active(now_utc())
    return [TrackSummaryOut(**row) for row in rows]


def rename_track(track_id: str, title: str) -> TrackRenamedOut | None:
    row = tracks_repo.rename_title(track_id, title)
    if not row:
        return None
    return TrackRenamedOut(**row)
