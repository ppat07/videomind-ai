"""
Lead capture model for email list building and nurture flows.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean

from database import Base


class Lead(Base):
    """Tracks email leads captured from homepage and pricing page."""

    __tablename__ = "leads"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, nullable=False, index=True, unique=True)
    source = Column(String, nullable=True)  # e.g. "homepage", "pricing_exit_intent"
    free_chapter_sent = Column(Boolean, default=False, nullable=False)
    nurture_sent = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    nurture_scheduled_at = Column(DateTime, nullable=True)
    nurture_sent_at = Column(DateTime, nullable=True)
