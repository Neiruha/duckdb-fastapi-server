# /srv/neiruha/lab/app/server/main.py
from fastapi import FastAPI, Depends, HTTPException, Header, Query, Request
from fastapi.responses import JSONResponse
from typing import Optional
import datetime

from .config import APP_TITLE, API_PREFIX, TOKENS
from .logging_utils import get_logger
from .schemas import (
    GetUserInfoIn, UserInfoOut, UserListOut
)
from .data.users import build_user_info, build_user_list
from .db.connection import get_conn  # <-- добавили

log = get_logger("api")
app = FastAPI(title=APP_TITLE)

# --- Корень ---
@app.get("/")
def root():
    return {
        "message": "🦋 Startup Lab API",
        "quote": "«Кто с чудовищами сражается, тому стоит следить, чтобы самому не стать чудовищем.» — Ф. Ницше",
        "health": "/api/v1/health",
        "docs": "/docs"
    }

# --- Startup safe-check: проверяем минимальное чтение из БД ---
@app.on_event("startup")
def startup_safe_check():
    log.info("SAFE-CHECK: verifying DB minimal read access...")
    try:
        with get_conn(True) as con:
            con.execute("SELECT user_id, display_name FROM users LIMIT 1").fetchone()
        log.info("SAFE-CHECK: OK")
    except Exception as e:
        msg = str(e)
        log.error(f"SAFE-CHECK FAILED: {msg}")
        raise SystemExit(f"Startup safe-check failed: {msg}")

# --- Простая middleware для логов запросов ---
@app.middleware("http")
async def log_requests(request: Request, call_next):
    path = request.url.path
    method = request.method
    try:
        response = await call_next(request)
        log.info(f"{method} {path} -> {response.status_code}")
        return response
    except Exception as e:
        log.exception(f"Unhandled error on {method} {path}: {e}")
        return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

# --- Auth helpers ---
def require_token(authorization: Optional[str] = Header(default=None, alias="Authorization")) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    token = authorization.replace("Bearer ", "").strip()
    role = TOKENS.get(token)
    if not role:
        raise HTTPException(status_code=403, detail="Invalid token")
    return role

def need_server_role(role: str = Depends(require_token)) -> str:
    if role != "server":
        raise HTTPException(status_code=403, detail="Server token required")
    return role

# --- Routes ---
@app.get(f"{API_PREFIX}/health")
def health():
    return {"ok": True, "ts": datetime.datetime.utcnow().isoformat() + "Z"}

@app.post(f"{API_PREFIX}/get_user_info", response_model=UserInfoOut)
def get_user_info(payload: GetUserInfoIn, role: str = Depends(require_token)):
    if not any([payload.user_id, payload.telegram_user_id, payload.telegram_user_name]):
        raise HTTPException(status_code=400, detail="Provide one of: user_id | telegram_user_id | telegram_user_name")
    data = build_user_info(payload.user_id, payload.telegram_user_id, payload.telegram_user_name)
    if not data:
        raise HTTPException(status_code=404, detail="User not found")
    return data

@app.get(f"{API_PREFIX}/get_user_list", response_model=UserListOut)
def get_user_list(
    role: str = Depends(need_server_role),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    return build_user_list(limit, offset)

# --- Global HTTPException handler ---
@app.exception_handler(HTTPException)
def http_exc_handler(request, exc: HTTPException):
    log.warning(f"HTTP {exc.status_code} on {request.url.path}: {exc.detail}")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

# --- Global unhandled Exception handler ---
@app.exception_handler(Exception)
def unhandled_exc_handler(request: Request, exc: Exception):
    msg = str(exc)
    if "Could not set lock on file" in msg or "Conflicting lock is held" in msg:
        log.warning(f"DB LOCK on {request.url.path}: {msg}")
        return JSONResponse(
            status_code=503,
            content={"detail": "DB_LOCKED", "hint": "Primary DB file is locked by another process."}
        )
    log.exception(f"Unhandled error on {request.url.path}: {msg}")
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})
