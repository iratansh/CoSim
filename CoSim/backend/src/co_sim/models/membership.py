from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from co_sim.db.base import Base
from co_sim.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class MembershipRole(str, enum.Enum):
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"


class Membership(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "memberships"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[MembershipRole] = mapped_column(Enum(MembershipRole), nullable=False, default=MembershipRole.VIEWER)

    user = relationship("User", back_populates="memberships")
    organization = relationship("Organization", back_populates="memberships")
