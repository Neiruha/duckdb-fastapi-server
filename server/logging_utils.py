# /srv/neiruha/lab/app/server/logging_utils.py
import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional
from .config import LOG_DIR, LOG_LEVEL

def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def get_logger(name: Optional[str] = None) -> logging.Logger:
    _ensure_dir(LOG_DIR)

    logger = logging.getLogger(name if name else "app")
    if logger.handlers:
        return logger  # уже инициализирован

    logger.setLevel(LOG_LEVEL)

    # Формат: время | уровень | модуль:строка | сообщение
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # В файл (ротация до ~5MB * 5)
    file_path = os.path.join(LOG_DIR, "server.log")
    fh = RotatingFileHandler(file_path, maxBytes=5_000_000, backupCount=5, encoding="utf-8")
    fh.setFormatter(fmt)
    fh.setLevel(LOG_LEVEL)

    # В консоль
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    ch.setLevel(LOG_LEVEL)

    logger.addHandler(fh)
    logger.addHandler(ch)
    logger.propagate = False

    return logger
