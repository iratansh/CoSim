from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from co_sim.db.base import Base
from co_sim.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Secret(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "secrets"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    value_encrypted: Mapped[str] = mapped_column(String(1024), nullable=False)

    workspace = relationship("Workspace", back_populates="secrets")
