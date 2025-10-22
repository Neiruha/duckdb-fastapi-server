from __future__ import annotations

from fastapi import APIRouter, Depends

from ..middleware.access import Caller, need_client_role, require_token
from ..schemas.sessions import (
    ClientTokenRefreshIn,
    ClientTokenRefreshOut,
    ClientTokenRevokeOut,
    MiniAppConnectIn,
    MiniAppConnectOut,
    SessionConnectIn,
    SessionDisconnectIn,
    SessionOut,
    SessionRefreshIn,
)
from ..services.sessions_service import (
    connect_miniapp_session,
    connect_session,
    disconnect_session,
    refresh_client_token,
    refresh_session,
    revoke_client_token,
)

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/connect", response_model=SessionOut)
def connect(payload: SessionConnectIn, caller: Caller = Depends(require_token(allow_demo=True))) -> SessionOut:  # noqa: ARG001
    return connect_session(payload)


@router.post("/refresh", response_model=SessionOut)
def refresh(payload: SessionRefreshIn, caller: Caller = Depends(require_token())) -> SessionOut:  # noqa: ARG001
    return refresh_session(payload)


@router.post("/disconnect")
def disconnect(payload: SessionDisconnectIn, caller: Caller = Depends(require_token())) -> dict:  # noqa: ARG001
    return disconnect_session(payload)


@router.post("/connect/miniapp", response_model=MiniAppConnectOut)
def connect_miniapp(payload: MiniAppConnectIn) -> MiniAppConnectOut:
    return connect_miniapp_session(payload)


@router.post("/client/revoke", response_model=ClientTokenRevokeOut)
def client_revoke(caller: Caller = Depends(need_client_role)) -> ClientTokenRevokeOut:
    return revoke_client_token(caller)


@router.post("/client/refresh", response_model=ClientTokenRefreshOut)
def client_refresh(
    payload: ClientTokenRefreshIn,
    caller: Caller = Depends(need_client_role),
) -> ClientTokenRefreshOut:
    return refresh_client_token(caller, payload)
