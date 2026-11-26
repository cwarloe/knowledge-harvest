-- Dedicated synthetic-only pilot schema. Intentionally no sample/client rows.
-- Run only against the separately created local kh_pilot database.
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

CREATE INDEX idx_recordings_creator ON recordings(creator);
CREATE INDEX idx_recordings_created_at ON recordings(created_at DESC);
CREATE INDEX idx_recordings_tags ON recordings USING GIN(tags);
