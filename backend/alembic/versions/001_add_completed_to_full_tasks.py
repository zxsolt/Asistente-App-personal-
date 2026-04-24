"""add completed to full_tasks

Revision ID: 001
Revises:
Create Date: 2026-04-16
"""
from alembic import op
import sqlalchemy as sa

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'full_tasks',
        sa.Column('completed', sa.Boolean(), nullable=False, server_default='0'),
    )


def downgrade() -> None:
    op.drop_column('full_tasks', 'completed')
