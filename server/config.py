from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Tuple

if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")

_config_log = logging.getLogger("config")


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or value == "":
        return ""
    return value


def _exit_with_config_error(message: str, **extra: object) -> None:
    parts = ["config", message]
    for key, val in extra.items():
        parts.append(f"{key}={val}")
    _config_log.critical(" ".join(parts))
    sys.exit(1)


APP_TITLE = os.getenv("APP_TITLE", "Startup Lab API")
API_PREFIX = os.getenv("API_PREFIX", "/api/v1")

SAFE_CHECK_ON_START = os.getenv("SAFE_CHECK_ON_START", "true").lower() in {"1", "true", "yes"}
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() in {"1", "true", "yes"}


DB_BACKEND = os.getenv("DB_BACKEND", "duckdb")  # 'duckdb' | 'postgres'

_duckdb_env = _require_env("DUCKDB_PATH")
if not _duckdb_env:
    _exit_with_config_error('db_error="duckdb_path_missing_or_not_found"', path="<missing>")
DUCKDB_PATH = _duckdb_env
_duckdb_file = Path(DUCKDB_PATH)
if not _duckdb_file.exists():
    _exit_with_config_error('db_error="duckdb_path_missing_or_not_found"', path=DUCKDB_PATH)

SANDBOX_DUCKDB_PATH = os.getenv("SANDBOX_DUCKDB_PATH", "/srv/neiruha/lab/app/data/_sandbox.duckdb")
POSTGRES_DSN = os.getenv("POSTGRES_DSN", "postgresql://user:pass@localhost:5432/neiruha")

MINIAPP_BOT_TOKEN = os.getenv("MINIAPP_BOT_TOKEN")

LOG_DIR = os.getenv("LOG_DIR", "/srv/neiruha/lab/app/server/logs")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

_tokens_env = _require_env("TOKENS_JSON")
if not _tokens_env:
    _exit_with_config_error('tokens_error="TOKENS_JSON missing or unreadable"', path="<missing>")
TOKENS_PATH = Path(_tokens_env)
if not TOKENS_PATH.exists():
    _exit_with_config_error('tokens_error="TOKENS_JSON missing or unreadable"', path=str(TOKENS_PATH))


def _read_tokens(path: Path) -> Dict[str, str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        _exit_with_config_error('tokens_error="empty_or_malformed"', path=str(path))
    if not isinstance(data, dict) or not data:
        _exit_with_config_error('tokens_error="empty_or_malformed"', path=str(path))
    return {str(k): str(v) for k, v in data.items()}


TOKENS: Dict[str, str] = _read_tokens(TOKENS_PATH)
TOKENS_COUNT = len(TOKENS)

DB_SERVER_USER = _require_env("DB_SERVER_USER")

SERVER_VERSION = _require_env("SERVER_VERSION")
if not SERVER_VERSION and SAFE_CHECK_ON_START:
    _exit_with_config_error('version_error="SERVER_VERSION missing"')

_version_json_path = Path(__file__).resolve().parent / "server" / "server" / "version.json"
VERSION_JSON_PATH = _version_json_path
BUILD_NAME: str | None = None
BUILD_DATETIME: str | None = None
BUILT_BY: str | None = None


def _load_version_info(path: Path) -> Tuple[str | None, str | None, str | None]:
    if not path.exists():
        if SAFE_CHECK_ON_START:
            _exit_with_config_error('version_error="version.json missing or invalid"', path=str(path))
        return None, None, None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        if SAFE_CHECK_ON_START:
            _exit_with_config_error('version_error="version.json missing or invalid"', path=str(path))
        return None, None, None
    build_name = payload.get("build_name")
    build_dt = payload.get("build_datetime")
    built_by = payload.get("built_by")
    if (not build_name or not build_dt) and SAFE_CHECK_ON_START:
        _exit_with_config_error('version_error="version.json missing or invalid"', path=str(path))
    return build_name, build_dt, built_by


BUILD_NAME, BUILD_DATETIME, BUILT_BY = _load_version_info(_version_json_path)

SESSION_MAX_TTL_MINUTES = 60 * 24 * 7
SESSION_MIN_TTL_MINUTES = 10


def emit_config_logs(logger: logging.Logger) -> None:
    logger.info("config tokens_loaded path=%s count=%s", str(TOKENS_PATH), TOKENS_COUNT)
    logger.info(
        "config duckdb_path=%s exists=%s",
        DUCKDB_PATH,
        str(_duckdb_file.exists()).lower(),
    )
    if BUILD_NAME and BUILD_DATETIME:
        logger.info(
            'config version_json name="%s" dt=%s by="%s"',
            BUILD_NAME,
            BUILD_DATETIME,
            BUILT_BY or "unknown",
        )


def reload_tokens() -> Dict[str, str]:
    return _read_tokens(TOKENS_PATH)
