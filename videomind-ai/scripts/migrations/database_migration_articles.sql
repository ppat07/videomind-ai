-- Migration to support articles in VideoMind AI directory
-- Extends existing directory_entries table to handle both videos and articles

-- Add new columns for article support
ALTER TABLE directory_entries 
ADD COLUMN content_type VARCHAR(20) DEFAULT 'video' NOT NULL;

ALTER TABLE directory_entries 
ADD COLUMN source_url VARCHAR(500);

ALTER TABLE directory_entries 
ADD COLUMN article_content TEXT;

ALTER TABLE directory_entries 
ADD COLUMN word_count INTEGER DEFAULT 0;

ALTER TABLE directory_entries 
ADD COLUMN reading_time_minutes INTEGER DEFAULT 0;

-- Migrate existing video_url to source_url
UPDATE directory_entries 
SET source_url = video_url, content_type = 'video' 
WHERE video_url IS NOT NULL;

-- Make video_url nullable and source_url the main field
-- (We'll keep video_url for backward compatibility but use source_url going forward)

-- Add index for content type filtering
CREATE INDEX IF NOT EXISTS idx_directory_entries_content_type ON directory_entries(content_type);
CREATE INDEX IF NOT EXISTS idx_directory_entries_source_url ON directory_entries(source_url);