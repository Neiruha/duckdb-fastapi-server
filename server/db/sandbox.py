from __future__ import annotations

import os
import re
import shutil
import threading
from typing import Any, List, Sequence, Tuple

import duckdb

from ..config import DUCKDB_PATH, SANDBOX_DUCKDB_PATH
from ..logging_utils import get_logger

log = get_logger("db.sandbox")

_SQL_PREFIX_PATTERN = re.compile(r"^(\s*)(select|with)\b", re.IGNORECASE | re.DOTALL)
_FORBIDDEN_PATTERN = re.compile(r"\b(attach|copy|pragma|export)\b", re.IGNORECASE)
_COMMENT_PATTERN = re.compile(r"--|/\*")

_cache_lock = threading.Lock()
_exec_lock = threading.Lock()
_cache: dict[str, Any] = {"src_mtime": None, "con": None}


def _validate_sql(sql: str) -> None:
    if not sql or not sql.strip():
        raise ValueError("SQL must not be empty")
    lower = sql.strip().lower()
    if ";" in lower:
        raise ValueError("Semicolons are not allowed")
    if _COMMENT_PATTERN.search(sql):
        raise ValueError("SQL comments are not allowed")
    if not _SQL_PREFIX_PATTERN.match(sql):
        raise ValueError("Only SELECT statements are allowed")
    if _FORBIDDEN_PATTERN.search(sql):
        raise ValueError("Forbidden statement in SQL")


def _ensure_copy_locked(src_mtime: float) -> duckdb.DuckDBPyConnection:
    existing = _cache.get("src_mtime")
    con = _cache.get("con")
    sandbox_path = SANDBOX_DUCKDB_PATH

    need_refresh = (
        con is None
        or existing != src_mtime
        or not os.path.exists(sandbox_path)
    )

    if not need_refresh:
        return con

    if con is not None:
        try:
            con.close()
        except Exception:  # pragma: no cover - defensive
            pass

    os.makedirs(os.path.dirname(sandbox_path), exist_ok=True)
    shutil.copy2(DUCKDB_PATH, sandbox_path)
    new_con = duckdb.connect(sandbox_path, read_only=True)
    _cache["con"] = new_con
    _cache["src_mtime"] = src_mtime
    log.info("Sandbox copy refreshed from %s", DUCKDB_PATH)
    return new_con


def ensure_copy_up_to_date() -> duckdb.DuckDBPyConnection:
    if not os.path.exists(DUCKDB_PATH):
        raise FileNotFoundError(f"Source database not found: {DUCKDB_PATH}")

    src_mtime = os.path.getmtime(DUCKDB_PATH)
    with _cache_lock:
        return _ensure_copy_locked(src_mtime)


def select(sql: str, params: Sequence[Any] | None = None) -> Tuple[List[str], List[List[Any]]]:
    _validate_sql(sql)
    with _exec_lock:
        con = ensure_copy_up_to_date()
        cur = con.execute(sql, params or [])
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
    normalized_rows = [list(row) for row in rows]
    return columns, normalized_rows
