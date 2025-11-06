-- Seed Data for Content Management System
-- This file contains sample data for development and testing

BEGIN;

-- Insert sample users
INSERT INTO users (username, email, password_hash, full_name, is_admin) VALUES
('admin', 'admin@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIvAprzZ3m', 'Admin User', TRUE),
('john_doe', 'john@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIvAprzZ3m', 'John Doe', FALSE),
('jane_smith', 'jane@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIvAprzZ3m', 'Jane Smith', FALSE)
ON CONFLICT (email) DO NOTHING;

-- Insert sample segments
INSERT INTO segments (name, description, user_id, criteria, member_count, status) VALUES
('Tech Enthusiasts', 'Users interested in technology and innovation', 2, '{"age_range": [25, 45], "interests": ["technology", "innovation", "gadgets"]}', 1250, 'active'),
('Fashion Lovers', 'Fashion-conscious individuals', 2, '{"age_range": [20, 40], "interests": ["fashion", "style", "trends"]}', 890, 'active'),
('Food Bloggers', 'Food enthusiasts and bloggers', 3, '{"age_range": [22, 50], "interests": ["food", "cooking", "recipes"]}', 560, 'paused');

-- Insert sample contents
INSERT INTO contents (title, content_text, content_type, segment_id, user_id, tone, keywords, status) VALUES
(
    'Latest Tech Innovations',
    'Discover the cutting-edge technology that''s changing the world! From AI to quantum computing, we''re living in an exciting era of innovation. #Tech #Innovation',
    'social_post',
    1,
    2,
    'Professional',
    ARRAY['technology', 'innovation', 'AI'],
    'published'
),
(
    'Spring Fashion Trends 2024',
    'Get ready for spring with these amazing fashion trends! Bright colors, sustainable fabrics, and bold patterns are in. Stay stylish! #Fashion #SpringTrends',
    'social_post',
    2,
    2,
    'Friendly',
    ARRAY['fashion', 'trends', 'spring'],
    'published'
),
(
    'Ultimate Guide to Italian Cuisine',
    'Learn the secrets of authentic Italian cooking with our comprehensive guide. From pasta to pizza, master the art of Italian cuisine.',
    'blog_article',
    3,
    3,
    'Friendly',
    ARRAY['food', 'italian', 'cooking'],
    'published'
),
(
    'Weekly Tech Newsletter',
    'Stay updated with the latest in technology. This week: AI breakthroughs, new gadgets, and startup success stories.',
    'email',
    1,
    2,
    'Professional',
    ARRAY['newsletter', 'technology', 'updates'],
    'draft'
);

-- Insert sample performance metrics
INSERT INTO performance_metrics (content_id, views, engagements, conversions, engagement_rate, conversion_rate) VALUES
(1, 12500, 650, 89, 5.2, 0.71),
(2, 8900, 401, 56, 4.5, 0.63),
(3, 15600, 748, 112, 4.8, 0.72);

-- Insert sample feedback
INSERT INTO feedback (content_id, user_id, rating, comment) VALUES
(1, 2, 5, 'Great content! Very informative and engaging.'),
(2, 3, 4, 'Love the fashion insights. Could use more examples.'),
(3, 2, 5, 'Excellent guide! Tried the recipes and they were amazing.');

-- Insert sample generation history
INSERT INTO generation_history (user_id, prompt, generated_content, parameters, model_version) VALUES
(2, 'Write a social post about AI innovation', 'Discover the latest innovations in AI technology! #AI #Tech', '{"tone": "professional", "length": 150, "temperature": 0.7}', 'gpt-4'),
(3, 'Create a blog intro about Italian food', 'Italian cuisine is more than just food - it''s a way of life...', '{"tone": "friendly", "length": 200, "temperature": 0.8}', 'gpt-4');

COMMIT;

-- Display summary
SELECT 'Seed data inserted successfully!' as status;
SELECT 'Users: ' || COUNT(*) as summary FROM users;
SELECT 'Segments: ' || COUNT(*) as summary FROM segments;
SELECT 'Contents: ' || COUNT(*) as summary FROM contents;
