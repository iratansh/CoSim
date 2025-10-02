"""Workspace file persistence

Revision ID: 0003_workspace_files
Revises: 0002_sessions
Create Date: 2025-10-02 01:20:00
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0003_workspace_files"
down_revision = "0002_sessions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workspace_files",
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
        sa.Column("path", sa.String(length=512), nullable=False),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("language", sa.String(length=32), nullable=True),
        sa.UniqueConstraint("workspace_id", "path", name="uq_workspace_file_path"),
    )

    op.create_index("ix_workspace_files_workspace_id", "workspace_files", ["workspace_id"])
    op.create_index("ix_workspace_files_path", "workspace_files", ["path"])


def downgrade() -> None:
    op.drop_index("ix_workspace_files_path", table_name="workspace_files")
    op.drop_index("ix_workspace_files_workspace_id", table_name="workspace_files")
    op.drop_table("workspace_files")

