from __future__ import annotations

import json
import os
from typing import Dict

APP_TITLE = os.getenv("APP_TITLE", "Startup Lab API")
API_PREFIX = os.getenv("API_PREFIX", "/api/v1")

SAFE_CHECK_ON_START = os.getenv("SAFE_CHECK_ON_START", "true").lower() in {"1", "true", "yes"}
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() in {"1", "true", "yes"}

SMOOTH_SERIES_INTERVAL = os.getenv("SMOOTH_SERIES_INTERVAL", "day").lower()
if SMOOTH_SERIES_INTERVAL not in {"day", "week"}:
    raise RuntimeError("SMOOTH_SERIES_INTERVAL must be either 'day' or 'week'")

try:
    SMOOTH_SERIES_MAX_POINTS = int(os.getenv("SMOOTH_SERIES_MAX_POINTS", "366"))
except ValueError as exc:  # pragma: no cover - configuration error
    raise RuntimeError("SMOOTH_SERIES_MAX_POINTS must be an integer") from exc

SMOOTH_GAP_STRATEGY = os.getenv("SMOOTH_GAP_STRATEGY", "linear").lower()
if SMOOTH_GAP_STRATEGY not in {"linear", "carry"}:
    raise RuntimeError("SMOOTH_GAP_STRATEGY must be either 'linear' or 'carry'")

try:
    SMOOTH_EMA_ALPHA = float(os.getenv("SMOOTH_EMA_ALPHA", "0.3"))
except ValueError as exc:  # pragma: no cover - configuration error
    raise RuntimeError("SMOOTH_EMA_ALPHA must be a float between 0 and 1") from exc
if not 0 < SMOOTH_EMA_ALPHA <= 1:
    raise RuntimeError("SMOOTH_EMA_ALPHA must be in the (0, 1] range")

SMOOTH_WEIGHTS = {
    "teacher": float(os.getenv("SMOOTH_WEIGHT_TEACHER", "0.5")),
    "mentor": float(os.getenv("SMOOTH_WEIGHT_MENTOR", "0.3")),
    "student": float(os.getenv("SMOOTH_WEIGHT_STUDENT", "0.2")),
}
total_weight = sum(SMOOTH_WEIGHTS.values())
if total_weight == 0:
    raise RuntimeError("SMOOTH_WEIGHTS must sum to a positive value")
SMOOTH_WEIGHTS = {k: v / total_weight for k, v in SMOOTH_WEIGHTS.items()}

DB_BACKEND = os.getenv("DB_BACKEND", "duckdb")  # 'duckdb' | 'postgres'
DUCKDB_PATH = os.getenv("DUCKDB_PATH", "/srv/neiruha/lab/app/data/neiruha.duckdb")
SANDBOX_DUCKDB_PATH = os.getenv(
    "SANDBOX_DUCKDB_PATH",
    "/srv/neiruha/lab/app/data/_sandbox.duckdb",
)
POSTGRES_DSN = os.getenv("POSTGRES_DSN", "postgresql://user:pass@localhost:5432/neiruha")

MINIAPP_BOT_TOKEN = os.getenv("MINIAPP_BOT_TOKEN")

LOG_DIR = os.getenv("LOG_DIR", "/srv/neiruha/lab/app/server/logs")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

_tokens_env = os.getenv("TOKENS_JSON")
if _tokens_env:
    try:
        TOKENS: Dict[str, str] = json.loads(_tokens_env)
    except json.JSONDecodeError as exc:  # pragma: no cover - configuration error
        raise RuntimeError("Failed to parse TOKENS_JSON") from exc
else:
    TOKENS = {
        "phil_token_zxcvbnhjaks": "server"
    }

SESSION_MAX_TTL_MINUTES = 60 * 24 * 7
SESSION_MIN_TTL_MINUTES = 10
