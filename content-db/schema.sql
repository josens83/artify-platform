-- Content Management Database Schema
-- Updated schema for campaign and creative management

-- ============================================
-- 정적 데이터 테이블
-- ============================================

-- Users Table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Campaigns Table
CREATE TABLE IF NOT EXISTS campaigns (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    objective VARCHAR(100),
    channel VARCHAR(100),
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Segments Table
CREATE TABLE IF NOT EXISTS segments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    filters JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ============================================
-- 동적 데이터 테이블
-- ============================================

-- Creatives Table
CREATE TABLE IF NOT EXISTS creatives (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER NOT NULL,
    segment_id INTEGER,
    copy_text TEXT,
    image_url TEXT,
    meta JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE,
    FOREIGN KEY (segment_id) REFERENCES segments(id) ON DELETE SET NULL
);

-- Generation Jobs Table
CREATE TABLE IF NOT EXISTS gen_jobs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    model VARCHAR(100),
    type VARCHAR(50),
    prompt TEXT,
    response TEXT,
    tokens INTEGER,
    cost DECIMAL(10, 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Metrics Table
CREATE TABLE IF NOT EXISTS metrics (
    id SERIAL PRIMARY KEY,
    creative_id INTEGER NOT NULL,
    date DATE NOT NULL,
    impressions INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    ctr DECIMAL(5, 2) DEFAULT 0.00,
    engagement INTEGER DEFAULT 0,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (creative_id) REFERENCES creatives(id) ON DELETE CASCADE
);

-- Feedbacks Table
CREATE TABLE IF NOT EXISTS feedbacks (
    id SERIAL PRIMARY KEY,
    creative_id INTEGER NOT NULL,
    source VARCHAR(100),
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (creative_id) REFERENCES creatives(id) ON DELETE CASCADE
);

-- ============================================
-- 인덱스
-- ============================================

-- Users 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- Campaigns 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_campaigns_user_id ON campaigns(user_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_channel ON campaigns(channel);
CREATE INDEX IF NOT EXISTS idx_campaigns_dates ON campaigns(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_campaigns_created_at ON campaigns(created_at);

-- Segments 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_segments_user_id ON segments(user_id);
CREATE INDEX IF NOT EXISTS idx_segments_name ON segments(name);
CREATE INDEX IF NOT EXISTS idx_segments_created_at ON segments(created_at);

-- Creatives 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_creatives_campaign_id ON creatives(campaign_id);
CREATE INDEX IF NOT EXISTS idx_creatives_segment_id ON creatives(segment_id);
CREATE INDEX IF NOT EXISTS idx_creatives_created_at ON creatives(created_at);

-- Gen Jobs 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_gen_jobs_user_id ON gen_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_gen_jobs_model ON gen_jobs(model);
CREATE INDEX IF NOT EXISTS idx_gen_jobs_type ON gen_jobs(type);
CREATE INDEX IF NOT EXISTS idx_gen_jobs_created_at ON gen_jobs(created_at);

-- Metrics 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_metrics_creative_id ON metrics(creative_id);
CREATE INDEX IF NOT EXISTS idx_metrics_date ON metrics(date);
CREATE INDEX IF NOT EXISTS idx_metrics_creative_date ON metrics(creative_id, date);

-- Feedbacks 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_feedbacks_creative_id ON feedbacks(creative_id);
CREATE INDEX IF NOT EXISTS idx_feedbacks_source ON feedbacks(source);
CREATE INDEX IF NOT EXISTS idx_feedbacks_created_at ON feedbacks(created_at);

-- ============================================
-- 트리거: updated_at 자동 업데이트
-- ============================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Campaigns 트리거
CREATE TRIGGER update_campaigns_updated_at
BEFORE UPDATE ON campaigns
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Segments 트리거
CREATE TRIGGER update_segments_updated_at
BEFORE UPDATE ON segments
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Creatives 트리거
CREATE TRIGGER update_creatives_updated_at
BEFORE UPDATE ON creatives
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 코멘트 (선택사항)
-- ============================================

COMMENT ON TABLE users IS '사용자 정보';
COMMENT ON TABLE campaigns IS '캠페인 정보';
COMMENT ON TABLE segments IS '타겟 세그먼트 정보';
COMMENT ON TABLE creatives IS '크리에이티브 (광고 소재)';
COMMENT ON TABLE gen_jobs IS 'AI 생성 작업 이력';
COMMENT ON TABLE metrics IS '크리에이티브 성과 지표';
COMMENT ON TABLE feedbacks IS '크리에이티브 피드백';

COMMENT ON COLUMN campaigns.objective IS '캠페인 목표 (awareness, consideration, conversion 등)';
COMMENT ON COLUMN campaigns.channel IS '캠페인 채널 (facebook, instagram, google 등)';
COMMENT ON COLUMN segments.filters IS '세그먼트 필터 조건 (JSON)';
COMMENT ON COLUMN creatives.meta IS '크리에이티브 메타데이터 (JSON)';
COMMENT ON COLUMN metrics.ctr IS 'Click-Through Rate (%)';
COMMENT ON COLUMN gen_jobs.tokens IS '사용된 토큰 수';
COMMENT ON COLUMN gen_jobs.cost IS '생성 비용 (USD)';
