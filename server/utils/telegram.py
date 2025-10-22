from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any, Dict
from urllib.parse import parse_qsl


class TelegramInitDataError(ValueError):
    """Raised when Telegram init data cannot be verified."""


def parse_webapp_init_data(init_data: str, bot_token: str) -> Dict[str, Any]:
    if not bot_token:
        raise TelegramInitDataError("Missing bot token for verification")

    try:
        pairs = parse_qsl(init_data, keep_blank_values=True, strict_parsing=True)
    except ValueError as exc:  # pragma: no cover - invalid input format
        raise TelegramInitDataError("Invalid init data format") from exc

    data: Dict[str, str] = {key: value for key, value in pairs}
    received_hash = data.pop("hash", None)
    if not received_hash:
        raise TelegramInitDataError("Missing hash field")

    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(data.items()))

    secret_key = hmac.new(  # Telegram rule for Web Apps
        key=b"WebAppData",
        msg=bot_token.encode(),
        digestmod=hashlib.sha256,
    ).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        raise TelegramInitDataError("Invalid init data signature")

    parsed_payload: Dict[str, Any] = {}
    for key, value in data.items():
        if value == "":
            parsed_payload[key] = value
            continue
        try:
            parsed_payload[key] = json.loads(value)
        except json.JSONDecodeError:
            parsed_payload[key] = value

    parsed_payload["hash"] = received_hash
    parsed_payload["raw"] = init_data
    return parsed_payload
