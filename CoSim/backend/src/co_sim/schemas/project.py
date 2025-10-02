from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from co_sim.schemas.base import TimestampedModel


class ProjectCreate(BaseModel):
    organization_id: UUID
    name: str = Field(max_length=120)
    slug: str = Field(max_length=120)
    description: Optional[str] = Field(default=None, max_length=500)
    template_id: Optional[UUID] = None
    settings: dict[str, object] = Field(default_factory=dict)


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=120)
    description: Optional[str] = Field(default=None, max_length=500)
    template_id: Optional[UUID] = None
    settings: Optional[dict[str, object]] = None


class ProjectRead(TimestampedModel):
    organization_id: UUID
    created_by_id: Optional[UUID]
    name: str
    slug: str
    description: Optional[str]
    template_id: Optional[UUID]
    settings: dict[str, object]
