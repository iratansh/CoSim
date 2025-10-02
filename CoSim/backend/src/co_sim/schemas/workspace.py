from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from co_sim.models.workspace import WorkspaceStatus
from co_sim.schemas.base import TimestampedModel


class WorkspaceCreate(BaseModel):
    project_id: UUID
    name: str = Field(max_length=120)
    slug: str = Field(max_length=120)
    template_id: Optional[UUID] = None
    requested_gpu: Optional[int] = Field(default=None, ge=0)
    settings: dict[str, object] = Field(default_factory=dict)


class WorkspaceUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=120)
    template_id: Optional[UUID] = None
    requested_gpu: Optional[int] = Field(default=None, ge=0)
    status: Optional[WorkspaceStatus] = None
    settings: Optional[dict[str, object]] = None


class WorkspaceRead(TimestampedModel):
    project_id: UUID
    template_id: Optional[UUID]
    name: str
    slug: str
    status: WorkspaceStatus
    requested_gpu: Optional[int]
    settings: dict[str, object]
