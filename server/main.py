from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from .config import (
    APP_TITLE,
    API_PREFIX,
    BUILD_DATETIME,
    BUILD_NAME,
    BUILT_BY,
    DB_BACKEND,
    DB_SERVER_USER,
    DUCKDB_PATH,
    LOG_LEVEL,
    SAFE_CHECK_ON_START,
    SERVER_VERSION,
    emit_config_logs,
    reload_tokens,
)
from .db.connection import get_conn
from .logging_utils import get_logger
from .routers import get_api_router

log = get_logger("api")
config_log = get_logger("config")

app = FastAPI(
    title=APP_TITLE,
    docs_url="/api/docs",
    redoc_url=None,
    openapi_url="/api/openapi.json",
)

app.include_router(get_api_router())


@app.get("/")
def root() -> dict:
    version = SERVER_VERSION or "unknown"
    build_name = BUILD_NAME or "unknown"
    build_dt = BUILD_DATETIME or "unknown"
    return {
        "message": "Startup Lab API",
        "version": version,
        "build": build_name,
        "build_datetime": build_dt,
        "api_prefix": API_PREFIX,
    }


@app.get("/api")
def api_root() -> dict:
    version = SERVER_VERSION or "unknown"
    build_name = BUILD_NAME or "unknown"
    build_dt = BUILD_DATETIME or "unknown"
    return {
        "message": "Startup Lab API",
        "version": version,
        "build": build_name,
        "build_datetime": build_dt,
        "api_prefix": API_PREFIX,
    }


@app.on_event("startup")
def startup_safe_check() -> None:
    emit_config_logs(config_log)

    build_name = BUILD_NAME or "unknown"
    build_dt = BUILD_DATETIME or "unknown"
    build_by = BUILT_BY or "unknown"
    version = SERVER_VERSION or "unknown"
    duckdb_exists = str(Path(DUCKDB_PATH).exists()).lower()

    log.info(
        'boot app="%s" version=%s build="%s" build_dt=%s by="%s"',
        APP_TITLE,
        version,
        build_name,
        build_dt,
        build_by,
    )
    log.info(
        "boot api_prefix=%s log_level=%s db_backend=%s duckdb_path=%s exists=%s",
        API_PREFIX,
        LOG_LEVEL,
        DB_BACKEND,
        DUCKDB_PATH,
        duckdb_exists,
    )

    if not SAFE_CHECK_ON_START:
        return

    run_safe_check()


def run_safe_check() -> None:
    try:
        tokens = reload_tokens()
    except SystemExit:
        log.critical("bootcheck tokens_ok=false")
        raise
    log.info("bootcheck tokens_ok=true count=%s", len(tokens))

    with get_conn(read_only=False) as con:
        admin_count = con.execute("SELECT COUNT(*) FROM user_roles WHERE role='admin'").fetchone()[0]
        if not admin_count:
            log.critical("bootcheck admin_present=false")
            sys.exit(1)
        log.info("bootcheck admin_present=true count=%s", admin_count)

        metrics_count = con.execute("SELECT COUNT(*) FROM metrics").fetchone()[0]
        if not metrics_count:
            log.critical("bootcheck metrics_count=0")
            sys.exit(1)
        log.info("bootcheck metrics_count=%s", metrics_count)

        if not DB_SERVER_USER:
            log.critical("bootcheck db_server_user_missing user=<missing>")
            sys.exit(1)

        try:
            con.execute("BEGIN")
            user_exists = con.execute(
                "SELECT COUNT(*) FROM users WHERE user_id = ?",
                [DB_SERVER_USER],
            ).fetchone()[0]
            if not user_exists:
                con.execute("ROLLBACK")
                log.critical("bootcheck db_server_user_missing user=%s", DB_SERVER_USER)
                sys.exit(1)

            con.execute(
                "UPDATE users SET last_connected = current_timestamp WHERE user_id = ?",
                [DB_SERVER_USER],
            )
            revoked_result = con.execute(
                "UPDATE sessions SET revoked_at = current_timestamp WHERE revoked_at IS NULL",
            )
            deleted_result = con.execute(
                "DELETE FROM sessions WHERE expires_at < current_timestamp",
            )
            con.execute("COMMIT")
        except Exception:
            con.execute("ROLLBACK")
            raise

        revoked_count = getattr(revoked_result, "rowcount", 0) or 0
        deleted_count = getattr(deleted_result, "rowcount", 0) or 0
        log.info(
            "bootcheck db_write_ok=true user=%s sessions_revoked=%s sessions_deleted=%s",
            DB_SERVER_USER,
            revoked_count,
            deleted_count,
        )

        con.execute(
            """
            CREATE TABLE IF NOT EXISTS metric_groups(
              group_id VARCHAR PRIMARY KEY,
              name VARCHAR NOT NULL,
              description VARCHAR,
              created_at TIMESTAMP DEFAULT (current_timestamp) NOT NULL,
              element_code VARCHAR,
              element_ru VARCHAR
            )
            """
        )
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS metric_group_members(
              group_id VARCHAR,
              metric_id VARCHAR,
              weight DOUBLE NOT NULL,
              PRIMARY KEY (group_id, metric_id),
              CHECK (weight >= 0 AND weight <= 1)
            )
            """
        )
        log.info("bootcheck metric_groups_ready=true")

        columns = {row[1] for row in con.execute("PRAGMA table_info('step_metric_scores')").fetchall()}
        value_column = "value_raw" if "value_raw" in columns else "value"
        stats_query = f"""
            SELECT
              mg.group_id,
              COUNT(s.{value_column}) AS n,
              MIN(s.{value_column})   AS v_min,
              AVG(s.{value_column})   AS v_avg,
              MAX(s.{value_column})   AS v_max
            FROM metric_groups mg
            JOIN metric_group_members gm ON gm.group_id = mg.group_id
            JOIN step_metric_scores s    ON s.metric_id = gm.metric_id
            GROUP BY mg.group_id
        """
        stats_rows = con.execute(stats_query).fetchall()

        if not stats_rows:
            log.info("bootcheck metric_group_stats none=true")
        else:
            for group_id, n, v_min, v_avg, v_max in stats_rows:
                log.info(
                    "bootcheck metric_group_stats group=%s n=%s min=%s avg=%s max=%s",
                    group_id,
                    n,
                    v_min,
                    v_avg,
                    v_max,
                )

        log.info(
            "bootcheck result=ok tokens=true admin=true metrics=%s db_write=true sessions_revoked=%s sessions_deleted=%s",
            metrics_count,
            revoked_count,
            deleted_count,
        )


@app.middleware("http")
async def log_requests(request: Request, call_next):
    path = request.url.path
    method = request.method
    try:
        response = await call_next(request)
        log.info("%s %s -> %s", method, path, response.status_code)
        return response
    except Exception as exc:  # pragma: no cover - safeguard
        log.exception("Unhandled error on %s %s: %s", method, path, exc)
        return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})


@app.exception_handler(HTTPException)
async def http_exc_handler(request: Request, exc: HTTPException):
    log.warning("HTTP %s on %s: %s", exc.status_code, request.url.path, exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def unhandled_exc_handler(request: Request, exc: Exception):
    msg = str(exc)
    if "Could not set lock on file" in msg or "Conflicting lock is held" in msg:
        log.warning("DB LOCK on %s: %s", request.url.path, msg)
        return JSONResponse(
            status_code=503,
            content={"detail": "DB_LOCKED", "hint": "Primary DB file is locked by another process."},
        )
    log.exception("Unhandled error on %s: %s", request.url.path, msg)
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})
