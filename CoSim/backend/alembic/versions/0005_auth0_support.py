"""Add Auth0 support to users table

Revision ID: 0005_auth0_support
Revises: 0004_user_plan
Create Date: 2025-10-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0005_auth0_support'
down_revision: Union[str, None] = '0004_user_plan'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make hashed_password nullable for Auth0 users
    op.alter_column('users', 'hashed_password',
                    existing_type=sa.String(256),
                    nullable=True)
    
    # Add external_id for Auth0 sub (e.g., 'auth0|xxxxx', 'google-oauth2|xxxxx')
    op.add_column('users', sa.Column('external_id', sa.String(256), nullable=True))
    op.create_index('ix_users_external_id', 'users', ['external_id'], unique=True)
    
    # Add email_verified flag
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    op.drop_column('users', 'email_verified')
    op.drop_index('ix_users_external_id', table_name='users')
    op.drop_column('users', 'external_id')
    
    # Make hashed_password non-nullable again
    op.alter_column('users', 'hashed_password',
                    existing_type=sa.String(256),
                    nullable=False)
