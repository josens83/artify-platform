"""RFP Value Features: Templates, Batch Generation, Multi-language

Revision ID: 003
Revises: 002
Create Date: 2025-11-07

Changes:
- Update segments table with prompt template fields
- Add prompt_templates table
- Add creative_templates table
- Add batch_generation_jobs table
- Add channel_presets table
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

# revision identifiers, used by Alembic
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    """Apply database migrations"""

    # 1. Update segments table with prompt template fields
    op.add_column('segments', sa.Column('tone', sa.String(100), nullable=True))
    op.add_column('segments', sa.Column('keywords', sa.Text(), nullable=True))
    op.add_column('segments', sa.Column('reference_urls', sa.Text(), nullable=True))
    op.add_column('segments', sa.Column('prompt_template', sa.Text(), nullable=True))

    # 2. Create prompt_templates table
    op.create_table(
        'prompt_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('template', sa.Text(), nullable=False),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('language', sa.String(10), nullable=False, server_default='en'),
        sa.Column('variables', JSON, nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_prompt_templates_id', 'prompt_templates', ['id'])
    op.create_index('ix_prompt_templates_user_id', 'prompt_templates', ['user_id'])

    # 3. Create creative_templates table
    op.create_table(
        'creative_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('preview_url', sa.Text(), nullable=True),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('layout_config', JSON, nullable=False),
        sa.Column('font_family', sa.String(100), nullable=True),
        sa.Column('font_sizes', JSON, nullable=True),
        sa.Column('color_palette', JSON, nullable=False),
        sa.Column('channel', sa.String(50), nullable=True),
        sa.Column('size', sa.String(50), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_creative_templates_id', 'creative_templates', ['id'])
    op.create_index('ix_creative_templates_user_id', 'creative_templates', ['user_id'])

    # 4. Create batch_generation_jobs table
    op.create_table(
        'batch_generation_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('segment_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('content_type', sa.String(50), nullable=False),
        sa.Column('count', sa.Integer(), nullable=False),
        sa.Column('prompt_template_id', sa.Integer(), nullable=True),
        sa.Column('creative_template_id', sa.Integer(), nullable=True),
        sa.Column('parameters', JSON, nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('progress', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_items', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('completed_items', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_items', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('creative_ids', JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['segment_id'], ['segments.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['prompt_template_id'], ['prompt_templates.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['creative_template_id'], ['creative_templates.id'], ondelete='SET NULL')
    )
    op.create_index('ix_batch_generation_jobs_id', 'batch_generation_jobs', ['id'])
    op.create_index('ix_batch_generation_jobs_campaign_id', 'batch_generation_jobs', ['campaign_id'])
    op.create_index('ix_batch_generation_jobs_segment_id', 'batch_generation_jobs', ['segment_id'])
    op.create_index('ix_batch_generation_jobs_user_id', 'batch_generation_jobs', ['user_id'])
    op.create_index('ix_batch_generation_jobs_status', 'batch_generation_jobs', ['status'])

    # 5. Create channel_presets table
    op.create_table(
        'channel_presets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('channel', sa.String(50), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('width', sa.Integer(), nullable=False),
        sa.Column('height', sa.Integer(), nullable=False),
        sa.Column('aspect_ratio', sa.String(20), nullable=False),
        sa.Column('recommended_text_length', sa.Integer(), nullable=True),
        sa.Column('recommended_hashtags', sa.Integer(), nullable=True),
        sa.Column('best_practices', JSON, nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_channel_presets_id', 'channel_presets', ['id'])
    op.create_index('ix_channel_presets_channel', 'channel_presets', ['channel'])

    # 6. Insert default channel presets
    op.execute("""
        INSERT INTO channel_presets (name, channel, type, width, height, aspect_ratio, recommended_text_length, recommended_hashtags, best_practices)
        VALUES
        ('Instagram Feed Post', 'instagram', 'feed', 1080, 1080, '1:1', 2200, 10, '["Use high-quality images", "Keep text concise", "Include call-to-action"]'),
        ('Instagram Story', 'instagram', 'story', 1080, 1920, '9:16', 2200, 5, '["Use full-screen vertical format", "Add interactive elements", "Keep text brief"]'),
        ('Instagram Reel', 'instagram', 'reel', 1080, 1920, '9:16', 2200, 8, '["Keep videos under 60s", "Add trending audio", "Use captions"]'),
        ('Facebook Feed Post', 'facebook', 'feed', 1200, 630, '1.91:1', 63206, 5, '["Use eye-catching images", "Keep text concise", "Include call-to-action"]'),
        ('Facebook Story', 'facebook', 'story', 1080, 1920, '9:16', 63206, 3, '["Use vertical format", "Add interactive elements", "Keep brief"]'),
        ('Twitter Post', 'twitter', 'post', 1200, 675, '16:9', 280, 2, '["Keep under 280 characters", "Use 1-2 hashtags", "Include media"]'),
        ('LinkedIn Post', 'linkedin', 'post', 1200, 627, '1.91:1', 3000, 3, '["Professional tone", "Value-driven content", "Engage with comments"]'),
        ('YouTube Thumbnail', 'youtube', 'thumbnail', 1280, 720, '16:9', 100, 0, '["High contrast text", "Clear focal point", "Readable at small sizes"]')
    """)


def downgrade():
    """Rollback database migrations"""

    # Drop tables in reverse order
    op.drop_table('channel_presets')
    op.drop_table('batch_generation_jobs')
    op.drop_table('creative_templates')
    op.drop_table('prompt_templates')

    # Remove columns from segments
    op.drop_column('segments', 'prompt_template')
    op.drop_column('segments', 'reference_urls')
    op.drop_column('segments', 'keywords')
    op.drop_column('segments', 'tone')
