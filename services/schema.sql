-- Database schema for Knowledge Harvest
CREATE TABLE recordings (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    tags TEXT[] DEFAULT '{}',
    creator VARCHAR(100) NOT NULL DEFAULT 'Anonymous',
    duration INTERVAL,
    s3_key VARCHAR(500) NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX idx_recordings_creator ON recordings(creator);
CREATE INDEX idx_recordings_created_at ON recordings(created_at DESC);
CREATE INDEX idx_recordings_tags ON recordings USING GIN(tags);

-- Insert sample data
INSERT INTO recordings (title, description, tags, creator, duration, s3_key, file_size, mime_type)
VALUES 
    (
        'API Integration Walkthrough',
        'Step-by-step guide for integrating external APIs',
        ARRAY['API', 'React', 'Integration'],
        'Sarah Chen',
        INTERVAL '8 minutes 42 seconds',
        'recordings/sample-api-walkthrough.webm',
        15728640,
        'video/webm'
    ),
    (
        'Security Onion Hunt Techniques',
        'Advanced threat hunting using custom Kibana queries',
        ARRAY['Security', 'Hunting', 'Kibana', 'SOC'],
        'Rachel Martinez',
        INTERVAL '12 minutes 30 seconds',
        'recordings/sample-security-hunt.webm',
        22456789,
        'video/webm'
    );
