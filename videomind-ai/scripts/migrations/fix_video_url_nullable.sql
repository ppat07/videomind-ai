-- Make video_url nullable to support articles
-- SQLite doesn't support ALTER COLUMN directly, so we need to recreate the table

-- Create a backup of the original table
ALTER TABLE directory_entries RENAME TO directory_entries_backup;

-- Create new table with nullable video_url
CREATE TABLE directory_entries (
    id VARCHAR(36) PRIMARY KEY,
    source_job_id VARCHAR(36),
    title VARCHAR(200) NOT NULL,
    source_url VARCHAR(500),
    content_type VARCHAR(20) DEFAULT 'video' NOT NULL,
    creator_name VARCHAR(100),
    video_url VARCHAR(500), -- Now nullable
    category_primary VARCHAR(100),
    difficulty VARCHAR(20),
    tools_mentioned VARCHAR(200),
    summary_5_bullets TEXT,
    best_for VARCHAR(200),
    article_content TEXT,
    word_count INTEGER DEFAULT 0,
    reading_time_minutes INTEGER DEFAULT 0,
    signal_score INTEGER DEFAULT 70,
    processing_status VARCHAR(20) DEFAULT 'pending',
    teaches_agent_to TEXT,
    prompt_template TEXT,
    execution_checklist TEXT,
    agent_training_script TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Copy data from backup
INSERT INTO directory_entries SELECT * FROM directory_entries_backup;

-- Drop backup table
DROP TABLE directory_entries_backup;

-- Recreate indexes
CREATE INDEX IF NOT EXISTS idx_directory_entries_content_type ON directory_entries(content_type);
CREATE INDEX IF NOT EXISTS idx_directory_entries_source_url ON directory_entries(source_url);