"""Initial schema

Revision ID: 001
Revises:
Create Date: 2025-01-07 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema to initial state"""

    # Create segments table
    op.create_table(
        'segments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('criteria', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_segments_id'), 'segments', ['id'], unique=False)

    # Create generated_content table
    op.create_table(
        'generated_content',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('content_type', sa.String(length=50), nullable=False),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('result', sa.Text(), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=True),
        sa.Column('cache_key', sa.String(length=255), nullable=True),
        sa.Column('is_cached_result', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_generated_content_id'), 'generated_content', ['id'], unique=False)
    op.create_index(op.f('ix_generated_content_cache_key'), 'generated_content', ['cache_key'], unique=False)

    # Create metrics table
    op.create_table(
        'metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('metric_name', sa.String(length=255), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_metrics_id'), 'metrics', ['id'], unique=False)

    # Create gen_jobs table
    op.create_table(
        'gen_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('job_type', sa.String(length=50), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('prompt_tokens', sa.Integer(), nullable=True),
        sa.Column('completion_tokens', sa.Integer(), nullable=True),
        sa.Column('total_tokens', sa.Integer(), nullable=True),
        sa.Column('estimated_cost', sa.Float(), nullable=True, default=0.0),
        sa.Column('status', sa.String(length=50), nullable=True, default='completed'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_gen_jobs_id'), 'gen_jobs', ['id'], unique=False)

    # Create user_quotas table
    op.create_table(
        'user_quotas',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('daily_text_quota', sa.Integer(), nullable=True, default=100),
        sa.Column('daily_image_quota', sa.Integer(), nullable=True, default=20),
        sa.Column('monthly_cost_cap', sa.Float(), nullable=True, default=50.0),
        sa.Column('daily_text_used', sa.Integer(), nullable=True, default=0),
        sa.Column('daily_image_used', sa.Integer(), nullable=True, default=0),
        sa.Column('monthly_cost_used', sa.Float(), nullable=True, default=0.0),
        sa.Column('last_daily_reset', sa.DateTime(), nullable=True),
        sa.Column('last_monthly_reset', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('user_id')
    )
    op.create_index(op.f('ix_user_quotas_user_id'), 'user_quotas', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade database schema (drop all tables)"""

    op.drop_index(op.f('ix_user_quotas_user_id'), table_name='user_quotas')
    op.drop_table('user_quotas')

    op.drop_index(op.f('ix_gen_jobs_id'), table_name='gen_jobs')
    op.drop_table('gen_jobs')

    op.drop_index(op.f('ix_metrics_id'), table_name='metrics')
    op.drop_table('metrics')

    op.drop_index(op.f('ix_generated_content_cache_key'), table_name='generated_content')
    op.drop_index(op.f('ix_generated_content_id'), table_name='generated_content')
    op.drop_table('generated_content')

    op.drop_index(op.f('ix_segments_id'), table_name='segments')
    op.drop_table('segments')
