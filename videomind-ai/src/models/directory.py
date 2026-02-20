"""
Directory models for searchable AI training content.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Text, Integer

from database import Base


class DirectoryEntry(Base):
    """Database model for training directory entries."""

    __tablename__ = "directory_entries"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source_job_id = Column(String, nullable=True, index=True)

    title = Column(String, nullable=False, index=True)
    video_url = Column(String, nullable=False, unique=True)
    creator_name = Column(String, nullable=True, index=True)

    category_primary = Column(String, nullable=False, default="Automation Workflows", index=True)
    difficulty = Column(String, nullable=False, default="Beginner", index=True)

    tools_mentioned = Column(Text, nullable=True)
    summary_5_bullets = Column(Text, nullable=True)
    best_for = Column(Text, nullable=True)

    signal_score = Column(Integer, nullable=False, default=70)
    processing_status = Column(String, nullable=False, default="processed", index=True)

    # Agent-teaching outputs
    teaches_agent_to = Column(Text, nullable=True)
    prompt_template = Column(Text, nullable=True)
    execution_checklist = Column(Text, nullable=True)
    agent_training_script = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
