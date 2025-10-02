from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from co_sim.schemas.base import TimestampedModel


PLAN_CHOICES = {"free", "student", "pro", "team", "enterprise"}


def _normalize_plan(value: str | None) -> str:
    if not value:
        return "free"
    plan = value.lower()
    if plan not in PLAN_CHOICES:
        return "free"
    return plan


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: Optional[str] = Field(default=None, max_length=120)
    plan: str = Field(default="free", max_length=50)

    @field_validator("plan", mode="before")
    @classmethod
    def validate_plan(cls, value: Any) -> str:
        return _normalize_plan(value if isinstance(value, str) else None)


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, max_length=120)
    password: Optional[str] = Field(default=None, min_length=8)
    is_active: Optional[bool] = None
    plan: Optional[str] = Field(default=None, max_length=50)

    @field_validator("plan", mode="before")
    @classmethod
    def validate_plan(cls, value: Any) -> Optional[str]:
        if value is None:
            return None
        return _normalize_plan(value)


class UserRead(TimestampedModel):
    email: EmailStr
    full_name: Optional[str]
    plan: str
    is_active: bool
    is_superuser: bool


class UserInDB(UserRead):
    hashed_password: str


class TokenPayload(BaseModel):
    sub: UUID
    exp: int
    scopes: str | None = None


class AccessToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
