"""Add segment_id to gen_jobs table

Revision ID: 006
Revises: 005
Create Date: 2025-11-11

This migration adds the segment_id column to gen_jobs table to track which segment was used for generation
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    """Add segment_id column to gen_jobs table"""

    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Get existing columns in gen_jobs table
    existing_columns = [col['name'] for col in inspector.get_columns('gen_jobs')]

    # Add segment_id column if missing
    if 'segment_id' not in existing_columns:
        op.add_column('gen_jobs', sa.Column('segment_id', sa.Integer(), nullable=True))


def downgrade():
    """Remove segment_id column from gen_jobs table"""

    op.drop_column('gen_jobs', 'segment_id')
