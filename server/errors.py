from __future__ import annotations

from fastapi import HTTPException, status

__all__ = [
    "NotFoundError",
    "ConflictError",
    "UnauthorizedError",
    "raise_not_found",
]


class NotFoundError(HTTPException):
    def __init__(self, detail: str = "Not found") -> None:
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ConflictError(HTTPException):
    def __init__(self, detail: str = "Conflict") -> None:
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class UnauthorizedError(HTTPException):
    def __init__(self, detail: str = "Unauthorized") -> None:
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


def raise_not_found(entity: str) -> None:
    raise NotFoundError(f"{entity} not found")
