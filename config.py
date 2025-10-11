# /srv/neiruha/lab/app/server/config.py
from typing import Dict
import os

APP_TITLE = "Startup Lab API"
API_PREFIX = "/api/v1"

SAFE_CHECK_ON_START = True  # при старте проверяем доступ к БД минимальным запросом


DB_BACKEND = os.getenv("DB_BACKEND", "duckdb")  # 'duckdb' | 'postgres'
DUCKDB_PATH = os.getenv("DUCKDB_PATH", "/srv/neiruha/lab/app/data/neiruha.duckdb")
POSTGRES_DSN = os.getenv("POSTGRES_DSN", "postgresql://user:pass@localhost:5432/neiruha")

# ---- ЛОГИ ----
LOG_DIR = os.getenv("LOG_DIR", "/srv/neiruha/lab/app/server/logs")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# ---- ТОКЕНЫ (временные до 20 октября) ----
TOKENS: Dict[str, str] = {
    "tg_bot_token_abcdef": "server",
    "miniapp_token_123456": "client",
    "phil_token_zxcvbn": "server",
}
