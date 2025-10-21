from __future__ import annotations

from typing import Optional

from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..config import DEMO_MODE, TOKENS

security = HTTPBearer(auto_error=False)


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
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    return None


def require_token(allow_demo: bool = False):
    def dependency(
        credentials: HTTPAuthorizationCredentials | None = Depends(security),
        authorization: Optional[str] = Header(default=None, alias="Authorization", include_in_schema=False),
    ) -> str:
        token = _extract_token(credentials, authorization)
        if token:
            role = TOKENS.get(token)
            if not role:
                raise HTTPException(status_code=403, detail="Invalid token")
            return role

        if allow_demo and DEMO_MODE:
            return "demo"

        raise HTTPException(status_code=401, detail="Missing Authorization header")

    return dependency


def need_server_role(role: str = Depends(require_token())) -> str:
    if role != "server":
        raise HTTPException(status_code=403, detail="Server token required")
    return role
