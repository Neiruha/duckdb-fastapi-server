"""API routers."""

from fastapi import APIRouter

from ..config import API_PREFIX
from . import dbalive, flags, health, profiles, scores, sessions, tracks, users

__all__ = ["get_api_router"]


def get_api_router() -> APIRouter:
    router = APIRouter()
    router.include_router(health.router, prefix=API_PREFIX)
    router.include_router(dbalive.router, prefix=API_PREFIX)
    router.include_router(sessions.router, prefix=API_PREFIX)
    router.include_router(flags.router, prefix=API_PREFIX)
    router.include_router(profiles.router, prefix=API_PREFIX)
    router.include_router(scores.router, prefix=API_PREFIX)
    router.include_router(tracks.router, prefix=API_PREFIX)
    router.include_router(users.router, prefix=API_PREFIX)
    return router
