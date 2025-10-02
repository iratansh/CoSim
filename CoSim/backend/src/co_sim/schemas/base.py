from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ORMModel(BaseModel):
    class Config:
        from_attributes = True


class TimestampedModel(ORMModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
