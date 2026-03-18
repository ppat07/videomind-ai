"""
Subscription models for VideoMind AI Pro.
Tracks Pro subscribers and free tier usage.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Integer, UniqueConstraint

from database import Base


class ProSubscriber(Base):
    """Tracks active Pro subscribers (populated via Stripe webhooks)."""

    __tablename__ = "pro_subscribers"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, nullable=False, index=True)
    stripe_customer_id = Column(String, nullable=True, index=True)
    stripe_subscription_id = Column(String, nullable=True, unique=True)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    cancelled_at = Column(DateTime, nullable=True)


class FreeTierUsage(Base):
    """
    Tracks free video processing uses per email per month.
    One row per (email, year_month) pair, incremented on each free use.
    """

    __tablename__ = "free_tier_usage"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, nullable=False, index=True)
    year_month = Column(String, nullable=False)  # e.g. "2026-03"
    count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (UniqueConstraint("email", "year_month", name="uq_free_tier_usage"),)


class ConversionEvent(Base):
    """Simple event log for tracking key conversion funnel steps."""

    __tablename__ = "conversion_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, nullable=True, index=True)
    event = Column(String, nullable=False)  # e.g. "video_processed", "limit_hit", "pricing_viewed", "subscribed"
    metadata_ = Column(String, nullable=True)  # JSON string for extra data
    created_at = Column(DateTime, default=datetime.utcnow)
