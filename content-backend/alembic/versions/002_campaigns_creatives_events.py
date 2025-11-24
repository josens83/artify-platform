"""Add campaigns, creatives, and events tables

Revision ID: 002
Revises: 001
Create Date: 2025-01-07 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add campaigns, creatives, and events tables"""

    # Create campaigns table
    op.create_table(
        'campaigns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('channel', sa.String(length=50), nullable=False),
        sa.Column('size', sa.String(length=50), nullable=True),
        sa.Column('segment_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True, server_default='draft'),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('budget', sa.Float(), nullable=True),
        sa.Column('metadata', JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['segment_id'], ['segments.id'], ondelete='SET NULL')
    )
    op.create_index(op.f('ix_campaigns_id'), 'campaigns', ['id'], unique=False)
    op.create_index(op.f('ix_campaigns_user_id'), 'campaigns', ['user_id'], unique=False)

    # Create creatives table
    op.create_table(
        'creatives',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('content_type', sa.String(length=50), nullable=False),
        sa.Column('content_text', sa.Text(), nullable=True),
        sa.Column('asset_url', sa.Text(), nullable=True),
        sa.Column('thumbnail_url', sa.Text(), nullable=True),
        sa.Column('prompt', sa.Text(), nullable=True),
        sa.Column('model', sa.String(length=100), nullable=True),
        sa.Column('size', sa.String(length=50), nullable=True),
        sa.Column('variant', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True, server_default='draft'),
        sa.Column('performance_score', sa.Float(), nullable=True),
        sa.Column('metadata', JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ondelete='CASCADE')
    )
    op.create_index(op.f('ix_creatives_id'), 'creatives', ['id'], unique=False)
    op.create_index(op.f('ix_creatives_campaign_id'), 'creatives', ['campaign_id'], unique=False)

    # Create events table
    op.create_table(
        'events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('creative_id', sa.Integer(), nullable=True),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('session_id', sa.String(length=255), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('referrer', sa.Text(), nullable=True),
        sa.Column('landing_url', sa.Text(), nullable=True),
        sa.Column('channel', sa.String(length=50), nullable=True),
        sa.Column('segment_id', sa.Integer(), nullable=True),
        sa.Column('metadata', JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['creative_id'], ['creatives.id'], ondelete='SET NULL')
    )
    op.create_index(op.f('ix_events_id'), 'events', ['id'], unique=False)
    op.create_index(op.f('ix_events_campaign_id'), 'events', ['campaign_id'], unique=False)
    op.create_index(op.f('ix_events_creative_id'), 'events', ['creative_id'], unique=False)
    op.create_index(op.f('ix_events_event_type'), 'events', ['event_type'], unique=False)
    op.create_index(op.f('ix_events_user_id'), 'events', ['user_id'], unique=False)
    op.create_index(op.f('ix_events_session_id'), 'events', ['session_id'], unique=False)
    op.create_index(op.f('ix_events_segment_id'), 'events', ['segment_id'], unique=False)
    op.create_index(op.f('ix_events_created_at'), 'events', ['created_at'], unique=False)


def downgrade() -> None:
    """Drop campaigns, creatives, and events tables"""

    op.drop_index(op.f('ix_events_created_at'), table_name='events')
    op.drop_index(op.f('ix_events_segment_id'), table_name='events')
    op.drop_index(op.f('ix_events_session_id'), table_name='events')
    op.drop_index(op.f('ix_events_user_id'), table_name='events')
    op.drop_index(op.f('ix_events_event_type'), table_name='events')
    op.drop_index(op.f('ix_events_creative_id'), table_name='events')
    op.drop_index(op.f('ix_events_campaign_id'), table_name='events')
    op.drop_index(op.f('ix_events_id'), table_name='events')
    op.drop_table('events')

    op.drop_index(op.f('ix_creatives_campaign_id'), table_name='creatives')
    op.drop_index(op.f('ix_creatives_id'), table_name='creatives')
    op.drop_table('creatives')

    op.drop_index(op.f('ix_campaigns_user_id'), table_name='campaigns')
    op.drop_index(op.f('ix_campaigns_id'), table_name='campaigns')
    op.drop_table('campaigns')
