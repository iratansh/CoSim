from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CollabParticipant(BaseModel):
    user_id: UUID
    role: str = Field(default="editor", max_length=50)


class CollabDocumentCreate(BaseModel):
    workspace_id: UUID
    name: str = Field(max_length=200)
    description: Optional[str] = Field(default=None, max_length=500)
    template_path: Optional[str] = Field(default=None)


class CollabDocumentRead(BaseModel):
    document_id: UUID
    workspace_id: UUID
    name: str
    description: Optional[str]
    template_path: Optional[str]
    participants: list[CollabParticipant] = Field(default_factory=list)
