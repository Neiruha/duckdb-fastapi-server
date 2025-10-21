from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ..middleware.access import need_server_role, require_token
from ..schemas.tracks import TrackSummaryOut
from ..schemas.users import TrackWithTeachersOut
from ..services.tracks_service import tracks_all_active, tracks_for_student, tracks_for_teacher

router = APIRouter(prefix="/tracks", tags=["tracks"])


@router.get("/teacher/{user_id}", response_model=list[TrackSummaryOut])
def teacher_tracks(
    user_id: str,
    active_only: bool = Query(True, description="Filter by active tracks only"),
    role: str = Depends(require_token()),  # noqa: ARG001
) -> list[TrackSummaryOut]:
    return tracks_for_teacher(user_id, active_only)


@router.get("/student/{user_id}", response_model=list[TrackWithTeachersOut])
def student_tracks(
    user_id: str,
    active_only: bool = Query(True, description="Filter by active tracks only"),
    role: str = Depends(require_token()),  # noqa: ARG001
) -> list[TrackWithTeachersOut]:
    return tracks_for_student(user_id, active_only)


@router.get("/active", response_model=list[TrackSummaryOut])
def active_tracks(role: str = Depends(need_server_role)) -> list[TrackSummaryOut]:  # noqa: ARG001
    return tracks_all_active()
