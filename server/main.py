from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from .config import APP_TITLE, API_PREFIX, SAFE_CHECK_ON_START
from .db.connection import get_conn
from .logging_utils import get_logger
from .routers import get_api_router

log = get_logger("api")

app = FastAPI(
    title=APP_TITLE,
    docs_url="/api/docs",
    redoc_url=None,
    openapi_url="/api/openapi.json",
)

app.include_router(get_api_router())


@app.get("/")
def root() -> dict:
    return {
        "message": "🦋 Startup Lab API",
        "health": f"{API_PREFIX}/health",
        "docs": "/api/docs",
    }


@app.get("/api")
def api_root() -> dict:
    return {
        "message": "🦋 Startup Lab API",
        "health": f"{API_PREFIX}/health",
        "docs": "/api/docs",
        "openapi": "/api/openapi.json",
    }


@app.on_event("startup")
def startup_safe_check() -> None:
    if not SAFE_CHECK_ON_START:
        return
    log.info("SAFE-CHECK: verifying DB minimal read access...")
    try:
        with get_conn(True) as con:
            con.execute("SELECT 1 FROM users LIMIT 1").fetchone()
        log.info("SAFE-CHECK: OK")
    except Exception as exc:  # pragma: no cover - startup guard
        msg = str(exc)
        log.error("SAFE-CHECK FAILED: %s", msg)
        raise SystemExit(f"Startup safe-check failed: {msg}") from exc


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
