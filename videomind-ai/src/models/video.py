"""
Video processing models and schemas.
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any

from sqlalchemy import Column, String, DateTime, Float, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import String as SQLString
from pydantic import BaseModel, HttpUrl, EmailStr, validator

from database import Base


class ProcessingStatus(str, Enum):
    """Video processing status options."""
    PENDING = "pending"
    DOWNLOADING = "downloading" 
    TRANSCRIBING = "transcribing"
    ENHANCING = "enhancing"
    COMPLETED = "completed"
    FAILED = "failed"


class ProcessingTier(str, Enum):
    """Processing tier options."""
    BASIC = "basic"
    DETAILED = "detailed"
    BULK = "bulk"


class VideoJob(Base):
    """Database model for video processing jobs."""
    
    __tablename__ = "video_jobs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    youtube_url = Column(String, nullable=False)
    status = Column(String, default=ProcessingStatus.PENDING.value)
    email = Column(String, nullable=False)
    tier = Column(String, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Processing results (stored as JSON)
    video_metadata = Column(JSON, nullable=True)  # Title, duration, etc.
    transcript = Column(JSON, nullable=True)      # Raw transcript with timestamps
    ai_enhanced = Column(JSON, nullable=True)     # Summaries, Q&As, etc.
    download_links = Column(JSON, nullable=True)  # Generated file paths
    
    # Business data
    cost = Column(Float, nullable=True)
    payment_intent_id = Column(String, nullable=True)  # Stripe payment ID
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(String, default="0")


# Pydantic schemas for API requests/responses

class VideoJobCreate(BaseModel):
    """Schema for creating a new video job."""
    youtube_url: HttpUrl  # Keep name for backwards compatibility
    email: EmailStr
    tier: ProcessingTier = ProcessingTier.BASIC
    
    @validator('youtube_url')
    def validate_video_url(cls, v):
        """Ensure URL is from supported platforms (YouTube or Rumble)."""
        url_str = str(v)
        supported_domains = ['youtube.com', 'youtu.be', 'rumble.com']
        if not any(domain in url_str for domain in supported_domains):
            raise ValueError('URL must be from YouTube or Rumble')
        return v


class VideoJobResponse(BaseModel):
    """Schema for video job responses."""
    id: str
    youtube_url: str
    status: ProcessingStatus
    email: str
    tier: ProcessingTier
    created_at: datetime
    completed_at: Optional[datetime]
    cost: Optional[float]
    error_message: Optional[str]
    download_links: Optional[Dict[str, str]]
    
    class Config:
        from_attributes = True


class VideoJobStatus(BaseModel):
    """Lightweight schema for status checks."""
    id: str
    status: ProcessingStatus
    progress_message: Optional[str]
    download_links: Optional[Dict[str, str]]
    error_message: Optional[str]