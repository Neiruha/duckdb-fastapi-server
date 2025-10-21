from __future__ import annotations

import secrets

__all__ = ["new_id"]


def new_id(prefix: str) -> str:
    """Generate a predictable identifier with a prefix and 24 hex chars."""

    if not prefix:
        raise ValueError("prefix is required")
    return f"{prefix}{secrets.token_hex(12)}"
