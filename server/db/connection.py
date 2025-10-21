# /srv/neiruha/lab/app/server/db/connection.py
from contextlib import contextmanager
from ..config import DB_BACKEND, DUCKDB_PATH, POSTGRES_DSN
from ..logging_utils import get_logger

log = get_logger("db")

@contextmanager
def get_conn(read_only: bool = True):
    if DB_BACKEND == "duckdb":
        import duckdb
        try:
            con = duckdb.connect(DUCKDB_PATH, read_only=read_only)
            log.debug(f"duckdb.connect({DUCKDB_PATH}, read_only={read_only}) ok")
            try:
                yield con
            finally:
                try:
                    con.close()
                except Exception:
                    pass
        except Exception as e:
            # Не скрываем — пробрасываем наверх, чтобы handler/стартап-чеки отреагировали
            log.exception(f"DuckDB connection error: {e}")
            raise
    elif DB_BACKEND == "postgres":
        raise NotImplementedError("Postgres backend is not enabled yet.")
    else:
        raise RuntimeError(f"Unsupported DB_BACKEND: {DB_BACKEND}")

def dictrows(cursor):
    cols = [d[0] for d in cursor.description]
    return [dict(zip(cols, r)) for r in cursor.fetchall()]
