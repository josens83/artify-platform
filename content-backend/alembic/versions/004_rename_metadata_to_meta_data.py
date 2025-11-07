"""Rename metadata to meta_data in Campaign, Creative, and Event tables

Revision ID: 004
Revises: 003
Create Date: 2025-11-07

Changes:
- Rename campaigns.metadata to campaigns.meta_data
- Rename creatives.metadata to creatives.meta_data
- Rename events.metadata to events.meta_data

This fixes SQLAlchemy reserved keyword conflict.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    """Apply database migrations"""

    # Rename metadata to meta_data in campaigns table
    op.alter_column('campaigns', 'metadata',
                    new_column_name='meta_data',
                    existing_type=sa.JSON(),
                    existing_nullable=True)

    # Rename metadata to meta_data in creatives table
    op.alter_column('creatives', 'metadata',
                    new_column_name='meta_data',
                    existing_type=sa.JSON(),
                    existing_nullable=True)

    # Rename metadata to meta_data in events table
    op.alter_column('events', 'metadata',
                    new_column_name='meta_data',
                    existing_type=sa.JSON(),
                    existing_nullable=True)


def downgrade():
    """Rollback database migrations"""

    # Rename meta_data back to metadata in events table
    op.alter_column('events', 'meta_data',
                    new_column_name='metadata',
                    existing_type=sa.JSON(),
                    existing_nullable=True)

    # Rename meta_data back to metadata in creatives table
    op.alter_column('creatives', 'meta_data',
                    new_column_name='metadata',
                    existing_type=sa.JSON(),
                    existing_nullable=True)

    # Rename meta_data back to metadata in campaigns table
    op.alter_column('campaigns', 'meta_data',
                    new_column_name='metadata',
                    existing_type=sa.JSON(),
                    existing_nullable=True)
