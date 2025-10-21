from __future__ import annotations

from fastapi import APIRouter, Depends

from ..middleware.access import require_token
from ..schemas.sessions import SessionConnectIn, SessionDisconnectIn, SessionOut, SessionRefreshIn
from ..services.sessions_service import connect_session, disconnect_session, refresh_session

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/connect", response_model=SessionOut)
def connect(payload: SessionConnectIn, role: str = Depends(require_token(allow_demo=True))) -> SessionOut:  # noqa: ARG001
    return connect_session(payload)


@router.post("/refresh", response_model=SessionOut)
def refresh(payload: SessionRefreshIn, role: str = Depends(require_token())) -> SessionOut:  # noqa: ARG001
    return refresh_session(payload)


@router.post("/disconnect")
def disconnect(payload: SessionDisconnectIn, role: str = Depends(require_token())) -> dict:  # noqa: ARG001
    return disconnect_session(payload)
