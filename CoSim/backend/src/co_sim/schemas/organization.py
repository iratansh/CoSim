from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from co_sim.schemas.base import TimestampedModel


class OrganizationCreate(BaseModel):
    name: str = Field(max_length=120)
    slug: str = Field(max_length=120)
    description: Optional[str] = Field(default=None, max_length=500)


class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=120)
    description: Optional[str] = Field(default=None, max_length=500)


class OrganizationRead(TimestampedModel):
    name: str
    slug: str
    description: Optional[str]
