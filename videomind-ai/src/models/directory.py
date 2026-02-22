"""
Directory models for searchable AI training content (videos + articles).
"""
import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Column, String, DateTime, Text, Integer, Enum as SqlEnum

from database import Base


class ContentType(Enum):
    """Supported content types in the directory."""
    VIDEO = "video"
    ARTICLE = "article"


class DirectoryEntry(Base):
    """Database model for training directory entries (videos + articles)."""

    __tablename__ = "directory_entries"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source_job_id = Column(String, nullable=True, index=True)

    # Content identification
    title = Column(String, nullable=False, index=True)
    source_url = Column(String, nullable=False, index=True)  # Video or article URL
    content_type = Column(SqlEnum(ContentType), nullable=False, default=ContentType.VIDEO, index=True)
    creator_name = Column(String, nullable=True, index=True)

    # Legacy field (keep for backward compatibility)
    video_url = Column(String, nullable=True, unique=True)

    # Content classification
    category_primary = Column(String, nullable=False, default="Automation Workflows", index=True)
    difficulty = Column(String, nullable=False, default="Beginner", index=True)

    # Content analysis
    tools_mentioned = Column(Text, nullable=True)
    summary_5_bullets = Column(Text, nullable=True)
    best_for = Column(Text, nullable=True)
    
    # Article-specific fields
    article_content = Column(Text, nullable=True)  # Full text content for articles
    word_count = Column(Integer, nullable=True, default=0)
    reading_time_minutes = Column(Integer, nullable=True, default=0)

    # Quality scoring
    signal_score = Column(Integer, nullable=False, default=70)
    processing_status = Column(String, nullable=False, default="processed", index=True)

    # Agent-teaching outputs
    teaches_agent_to = Column(Text, nullable=True)
    prompt_template = Column(Text, nullable=True)
    execution_checklist = Column(Text, nullable=True)
    agent_training_script = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def is_video(self) -> bool:
        """Check if this entry is a video."""
        return self.content_type == ContentType.VIDEO

    @property
    def is_article(self) -> bool:
        """Check if this entry is an article."""
        return self.content_type == ContentType.ARTICLE

    @property
    def display_url(self) -> str:
        """Get the primary URL for display (backward compatible)."""
        return self.source_url or self.video_url

    def __repr__(self):
        return f"<DirectoryEntry(id='{self.id}', type='{self.content_type.value}', title='{self.title}')>"