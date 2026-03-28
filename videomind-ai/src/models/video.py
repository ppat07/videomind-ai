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
from pydantic import BaseModel, HttpUrl, EmailStr, Field, validator

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
    video_url: HttpUrl = Field(..., alias="youtube_url")  # Accept both field names
    email: EmailStr
    tier: ProcessingTier = ProcessingTier.BASIC

    class Config:
        populate_by_name = True  # Allow both 'video_url' and 'youtube_url'

    @validator('video_url', pre=True)
    def validate_video_url(cls, v):
        """Ensure URL is HTTPS and from a domain yt-dlp can handle."""
        url_str = str(v)
        if not url_str.startswith('https://'):
            raise ValueError('Only HTTPS video URLs are supported')
        return v


class VideoJobResponse(BaseModel):
    """Schema for video job responses."""
    id: str
    video_url: str = Field(..., alias="youtube_url")  # DB column is still youtube_url
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
        populate_by_name = True


class VideoJobStatus(BaseModel):
    """Lightweight schema for status checks."""
    id: str
    status: ProcessingStatus
    progress_message: Optional[str]
    download_links: Optional[Dict[str, str]]
    error_message: Optional[str]