from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from co_sim.models.template import TemplateKind
from co_sim.schemas.base import TimestampedModel


class TemplateCreate(BaseModel):
    name: str = Field(max_length=120)
    kind: TemplateKind
    description: Optional[str] = Field(default=None, max_length=500)
    config: dict[str, object] = Field(default_factory=dict)


class TemplateUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=120)
    description: Optional[str] = Field(default=None, max_length=500)
    config: Optional[dict[str, object]] = None


class TemplateRead(TimestampedModel):
    name: str
    kind: TemplateKind
    description: Optional[str]
    config: dict[str, object]
