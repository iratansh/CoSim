"""Session orchestration tables

Revision ID: 0002_sessions
Revises: 0001
Create Date: 2024-06-01 12:00:00
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002_sessions"
down_revision = "0001"
branch_labels = None
depends_on = None

SESSION_TYPE = sa.Enum(
    "ide",
    "simulator",
    name="session_type_enum",
    native_enum=False,
)

SESSION_STATUS = sa.Enum(
    "pending",
    "starting",
    "running",
    "paused",
    "terminating",
    "terminated",
    name="session_status_enum",
    native_enum=False,
)


def upgrade() -> None:
    op.create_table(
        "sessions",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column(
            "workspace_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("session_type", SESSION_TYPE, nullable=False, server_default="ide"),
        sa.Column("status", SESSION_STATUS, nullable=False, server_default="pending"),
        sa.Column("requested_gpu", sa.Integer(), nullable=True),
        sa.Column("details", sa.dialects.postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_index("ix_sessions_workspace_id", "sessions", ["workspace_id"])

    op.create_table(
        "session_participants",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column(
            "session_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(length=50), nullable=False, server_default="editor"),
    )

    op.create_index("ix_session_participants_session_id", "session_participants", ["session_id"])
    op.create_index("ix_session_participants_user_id", "session_participants", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_session_participants_user_id", table_name="session_participants")
    op.drop_index("ix_session_participants_session_id", table_name="session_participants")
    op.drop_table("session_participants")

    op.drop_index("ix_sessions_workspace_id", table_name="sessions")
    op.drop_table("sessions")
