from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass

# Import models to ensure they are registered with SQLAlchemy metadata.
from co_sim.models import (
    api_key,
    dataset,
    membership,
    organization,
    project,
    secret,
    session,
    template,
    user,
    workspace,
    workspace_file,
)  # noqa: F401
