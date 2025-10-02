from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from co_sim.schemas.base import TimestampedModel


class DatasetCreate(BaseModel):
    organization_id: UUID
    name: str = Field(max_length=120)
    uri: str = Field(max_length=500)
    description: Optional[str] = Field(default=None, max_length=500)


class DatasetUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=120)
    uri: Optional[str] = Field(default=None, max_length=500)
    description: Optional[str] = Field(default=None, max_length=500)


class DatasetRead(TimestampedModel):
    organization_id: UUID
    name: str
    uri: str
    description: Optional[str]
