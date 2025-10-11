# /srv/neiruha/lab/app/server/data/users.py
from typing import Optional, Dict, Any, List
from ..dbaware import user_repo
from ..logging_utils import get_logger

log = get_logger("data.users")

def build_user_info(
    user_id: Optional[str],
    telegram_user_id: Optional[int],
    telegram_user_name: Optional[str],
) -> Dict[str, Any]:
    user = user_repo.find_user(user_id, telegram_user_id, telegram_user_name)
    if not user:
        log.info("build_user_info: user not found")
        return {}

    curator_raw = user_repo.get_curator(user.get("mentor_user_id"))
    curator = {
        "user_id": curator_raw.get("user_id") if curator_raw else None,
        "display_name": curator_raw.get("display_name") if curator_raw else None,
        "telegram_username": curator_raw.get("telegram_username") if curator_raw else None,
    }

    tracks = user_repo.get_active_tracks_for_student(user["user_id"])
    active_tracks: List[Dict[str, Any]] = []
    for tr in tracks:
        teachers = user_repo.get_teachers_for_track(tr["track_id"])
        active_tracks.append({
            "track_id": tr["track_id"],
            "title": tr["title"],
            "status": tr["status"],
            "teachers": teachers
        })

    result = {
        "user_id": user["user_id"],
        "display_name": user["display_name"],
        "telegram_id": user["telegram_id"],
        "telegram_username": user["telegram_username"],
        "telegram_login_name": user["telegram_login_name"],
        "curator": curator,
        "active_tracks": active_tracks
    }
    log.debug(f"build_user_info -> tracks={len(active_tracks)}")
    return result

def build_user_list(limit: int, offset: int) -> Dict[str, Any]:
    data = user_repo.list_users(limit, offset)
    for it in data["items"]:
        if it["last_seen_at"] is not None:
            it["last_seen_at"] = str(it["last_seen_at"])
    log.debug(f"build_user_list -> {len(data['items'])} items")
    return data
