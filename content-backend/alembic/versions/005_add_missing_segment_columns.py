"""Add missing columns to segments table

Revision ID: 005
Revises: 004
Create Date: 2025-11-10

This migration safely adds missing columns to existing segments table
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    """Add missing columns if they don't exist"""

    # Check and add columns one by one with error handling
    # This allows migration to succeed even if some columns already exist

    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Get existing columns
    existing_columns = [col['name'] for col in inspector.get_columns('segments')]

    # Add criteria if missing (from original schema)
    if 'criteria' not in existing_columns:
        op.add_column('segments', sa.Column('criteria', sa.Text(), nullable=True))

    # Add description if missing (from original schema)
    if 'description' not in existing_columns:
        op.add_column('segments', sa.Column('description', sa.Text(), nullable=True))

    # Add created_at if missing (from original schema)
    if 'created_at' not in existing_columns:
        op.add_column('segments', sa.Column('created_at', sa.DateTime(), nullable=True))

    # Add updated_at if missing (from original schema)
    if 'updated_at' not in existing_columns:
        op.add_column('segments', sa.Column('updated_at', sa.DateTime(), nullable=True))

    # Add tone if missing (from RFP features)
    if 'tone' not in existing_columns:
        op.add_column('segments', sa.Column('tone', sa.String(100), nullable=True))

    # Add keywords if missing (from RFP features)
    if 'keywords' not in existing_columns:
        op.add_column('segments', sa.Column('keywords', sa.Text(), nullable=True))

    # Add reference_urls if missing (from RFP features)
    if 'reference_urls' not in existing_columns:
        op.add_column('segments', sa.Column('reference_urls', sa.Text(), nullable=True))

    # Add prompt_template if missing (from RFP features)
    if 'prompt_template' not in existing_columns:
        op.add_column('segments', sa.Column('prompt_template', sa.Text(), nullable=True))


def downgrade():
    """Remove added columns"""

    op.drop_column('segments', 'prompt_template')
    op.drop_column('segments', 'reference_urls')
    op.drop_column('segments', 'keywords')
    op.drop_column('segments', 'tone')
    op.drop_column('segments', 'updated_at')
    op.drop_column('segments', 'created_at')
    op.drop_column('segments', 'description')
    op.drop_column('segments', 'criteria')
