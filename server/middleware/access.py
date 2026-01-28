from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..config import DEMO_MODE, TOKENS
from ..db import client_tokens_repo
from ..utils.time import ensure_naive_utc, now_utc

security = HTTPBearer(auto_error=False)


@dataclass(slots=True)
class Caller:
    kind: Literal["server", "client", "demo"]
    user_id: str | None = None
    telegram_user_id: int | None = None
    token_id: str | None = None
    act_as_user_id: str | None = None
    act_as_telegram_user_id: int | None = None


def _extract_token(
    credentials: HTTPAuthorizationCredentials | None,
    authorization: Optional[str],
) -> Optional[str]:
    if credentials and credentials.scheme and credentials.scheme.lower() == "bearer":
        return credentials.credentials.strip()
    if authorization:
        lower = authorization.lower()
        if lower.startswith("bearer "):
            return authorization[7:].strip()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid Authorization header")
    return None


def _validate_client_token(token: str) -> Caller:
    row = client_tokens_repo.get_token(token)
    if not row:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    if row.get("revoked_at"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")

    expires_at = row.get("expires_at")
    if expires_at is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    current_naive = ensure_naive_utc(now_utc())
    if expires_at < current_naive:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")

    if row.get("user_banned"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="ACCOUNT_BANNED")

    if row.get("user_frozen"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="ACCOUNT_FROZEN")

    return Caller(
        kind="client",
        user_id=row.get("user_id"),
        telegram_user_id=row.get("telegram_user_id"),
        token_id=row.get("token_id"),
    )


def require_token(
    *,
    allow_server: bool = True,
    allow_client: bool = False,
    allow_demo: bool = False,
):
    def dependency(
        credentials: HTTPAuthorizationCredentials | None = Depends(security),
        authorization: Optional[str] = Header(default=None, alias="Authorization", include_in_schema=False),
        act_as_user_id: str | None = Header(default=None, alias="X-Act-As-User-Id"),
        act_as_telegram_user_id: int | None = Header(default=None, alias="X-Act-As-Telegram-User-Id"),
    ) -> Caller:
        token = _extract_token(credentials, authorization)
        if token:
            if token.startswith("ct_"):
                if not allow_client:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Client token not allowed")
                return _validate_client_token(token)

            role = TOKENS.get(token)
            if role == "server":
                if not allow_server:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Server token not allowed")
                return Caller(
                    kind="server",
                    act_as_user_id=act_as_user_id,
                    act_as_telegram_user_id=act_as_telegram_user_id,
                )

            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token")

        if allow_demo and DEMO_MODE:
            return Caller(kind="demo")

        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")

    return dependency


def need_server_role(caller: Caller = Depends(require_token())) -> Caller:
    if caller.kind != "server":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Server token required")
    return caller


def need_client_role(caller: Caller = Depends(require_token(allow_client=True, allow_server=False))) -> Caller:
    if caller.kind != "client":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Client token required")
    return caller


