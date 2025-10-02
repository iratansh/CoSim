from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from jose import jwt

from co_sim.core.config import settings


def create_access_token(subject: UUID, scopes: str | None = None, expires_delta: timedelta | None = None) -> tuple[str, int]:
    expire_delta = expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    expire = datetime.now(timezone.utc) + expire_delta
    to_encode: dict[str, Any] = {"sub": str(subject), "exp": expire}
    if scopes:
        to_encode["scopes"] = scopes
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt, int(expire_delta.total_seconds())


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
