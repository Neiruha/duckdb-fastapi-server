# /srv/neiruha/lab/app/server/dbaware/user_repo.py
from typing import Optional, Dict, Any, List
from ..db.connection import get_conn, dictrows
from ..logging_utils import get_logger

log = get_logger("repo.user")

def find_user(
    user_id: Optional[str],
    telegram_user_id: Optional[int],
    telegram_user_name: Optional[str],
) -> Optional[Dict[str, Any]]:
    where = []
    params: List[Any] = []
    if user_id:
        where.append("u.user_id = ?")
        params.append(user_id)
    if telegram_user_id is not None:
        where.append("u.telegram_id = ?")
        params.append(telegram_user_id)
    if telegram_user_name:
        where.append("(u.telegram_username = ? OR u.telegram_login_name = ?)")
        params.extend([telegram_user_name, telegram_user_name])

    if not where:
        log.warning("find_user called without any identifier")
        return None

    sql = f"""
        SELECT u.user_id, u.display_name, u.telegram_id, u.telegram_username,
               u.telegram_login_name, u.mentor_user_id
        FROM users u
        WHERE {" OR ".join(where)}
        LIMIT 1
    """
    with get_conn(True) as con:
        cur = con.execute(sql, params)
        rows = dictrows(cur)
    log.debug(f"find_user -> {bool(rows)}")
    return rows[0] if rows else None

def get_curator(mentor_user_id: Optional[str]) -> Optional[Dict[str, Any]]:
    if not mentor_user_id:
        return None
    with get_conn(True) as con:
        cur = con.execute("""
            SELECT user_id, display_name, telegram_username
            FROM users
            WHERE user_id = ?
            LIMIT 1
        """, [mentor_user_id])
        rows = dictrows(cur)
    log.debug(f"get_curator({mentor_user_id}) -> {bool(rows)}")
    return rows[0] if rows else None

def get_active_tracks_for_student(student_user_id: str) -> List[Dict[str, Any]]:
    sql_tracks = """
        WITH my_tracks AS (
            SELECT tp.track_id
            FROM track_participants tp
            JOIN tracks t ON t.track_id = tp.track_id
            WHERE tp.user_id = ?
              AND tp.role_in_track = 'student'
              AND t.status = 'active'
              AND (t.end_at IS NULL OR t.end_at > CURRENT_TIMESTAMP)
        )
        SELECT t.track_id, t.title, t.status
        FROM tracks t
        JOIN my_tracks mt ON mt.track_id = t.track_id
        ORDER BY t.created_at DESC
    """
    with get_conn(True) as con:
        cur = con.execute(sql_tracks, [student_user_id])
        tracks = dictrows(cur)
    log.debug(f"get_active_tracks_for_student({student_user_id}) -> {len(tracks)} tracks")
    return tracks

def get_teachers_for_track(track_id: str) -> List[Dict[str, Any]]:
    with get_conn(True) as con:
        cur = con.execute("""
            SELECT u.user_id, u.display_name, u.telegram_username
            FROM track_participants tp
            JOIN users u ON u.user_id = tp.user_id
            WHERE tp.track_id = ?
              AND tp.role_in_track = 'teacher'
            ORDER BY tp.joined_at ASC
        """, [track_id])
        teachers = dictrows(cur)
    log.debug(f"get_teachers_for_track({track_id}) -> {len(teachers)} teachers")
    return teachers

def list_users(limit: int, offset: int) -> Dict[str, Any]:
    with get_conn(True) as con:
        sql = f"""
            WITH last_seen AS (
                SELECT user_id, MAX(created_at) AS last_seen_at
                FROM sessions
                GROUP BY user_id
            )
            SELECT u.user_id,
                   u.display_name,
                   u.telegram_id,
                   u.telegram_username,
                   u.web_login,
                   ls.last_seen_at
            FROM users u
            LEFT JOIN last_seen ls ON ls.user_id = u.user_id
            ORDER BY COALESCE(ls.last_seen_at, TIMESTAMP '1970-01-01') DESC, u.created_at DESC
            LIMIT {limit} OFFSET {offset}
        """
        cur = con.execute(sql)
        items = dictrows(cur)
        total = con.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    log.debug(f"list_users(limit={limit}, offset={offset}) -> {len(items)}/{total}")
    return {"total": total, "items": items}
