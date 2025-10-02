"""Add plan column to users

Revision ID: 0004_user_plan
Revises: 0003_workspace_files
Create Date: 2025-10-02 02:15:00
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0004_user_plan"
down_revision = "0003_workspace_files"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("plan", sa.String(length=50), nullable=False, server_default="free"),
    )
    op.execute("UPDATE users SET plan = 'free' WHERE plan IS NULL")
    op.alter_column("users", "plan", server_default="free")


def downgrade() -> None:
    op.drop_column("users", "plan")

