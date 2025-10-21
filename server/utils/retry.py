from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")

__all__ = ["with_retries"]


def with_retries(fn: Callable[[], T], attempts: int = 3, delay: float = 0.1) -> T:
    """Run callable with retries and exponential backoff."""

    exc: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except Exception as error:  # pragma: no cover - simple helper
            exc = error
            if attempt == attempts:
                break
            time.sleep(delay * attempt)
    assert exc is not None
    raise exc
