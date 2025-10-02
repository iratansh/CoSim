from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from co_sim.models.session import SessionStatus, SessionType
from co_sim.schemas.base import TimestampedModel


class SessionCreate(BaseModel):
    workspace_id: UUID
    session_type: SessionType = Field(default=SessionType.IDE)
    requested_gpu: Optional[int] = Field(default=None, ge=0)
    details: dict[str, object] = Field(default_factory=dict)


class SessionUpdate(BaseModel):
    status: Optional[SessionStatus] = None
    requested_gpu: Optional[int] = Field(default=None, ge=0)
    details: Optional[dict[str, object]] = None


class SessionParticipantCreate(BaseModel):
    user_id: UUID
    role: str = Field(default="editor", max_length=50)


class SessionParticipantRead(TimestampedModel):
    session_id: UUID
    user_id: UUID
    role: str


class SessionRead(TimestampedModel):
    workspace_id: UUID
    session_type: SessionType
    status: SessionStatus
    requested_gpu: Optional[int]
    details: dict[str, object]
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    participants: list[SessionParticipantRead] = Field(default_factory=list)
