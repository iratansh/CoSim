from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from co_sim.schemas.base import TimestampedModel


class SecretCreate(BaseModel):
    workspace_id: UUID
    name: str = Field(max_length=120)
    value: str = Field(max_length=1024)


class SecretRead(TimestampedModel):
    workspace_id: UUID
    name: str


class SecretReveal(SecretRead):
    value: str


class SecretRotate(BaseModel):
    value: str = Field(max_length=1024)
    description: Optional[str] = None
