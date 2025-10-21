from __future__ import annotations

import json
import os
from typing import Dict

APP_TITLE = os.getenv("APP_TITLE", "Startup Lab API")
API_PREFIX = os.getenv("API_PREFIX", "/api/v1")

SAFE_CHECK_ON_START = os.getenv("SAFE_CHECK_ON_START", "true").lower() in {"1", "true", "yes"}
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() in {"1", "true", "yes"}

DB_BACKEND = os.getenv("DB_BACKEND", "duckdb")  # 'duckdb' | 'postgres'
DUCKDB_PATH = os.getenv("DUCKDB_PATH", "/srv/neiruha/lab/app/data/neiruha.duckdb")
POSTGRES_DSN = os.getenv("POSTGRES_DSN", "postgresql://user:pass@localhost:5432/neiruha")

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
        "tg_bot_token_abcdef": "server",
        "miniapp_token_123456": "client",
        "phil_token_zxcvbnhjaks": "server",
    }

SESSION_MAX_TTL_MINUTES = 60 * 24 * 7
SESSION_MIN_TTL_MINUTES = 10
