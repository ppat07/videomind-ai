"""
Lead capture endpoint: email signup → free chapter delivery via SendGrid.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from config import settings
from database import get_database
from models.leads import Lead

router = APIRouter()

FREE_CHAPTER_URL = "https://videomind.ai/static/free-chapter.pdf"


class LeadCaptureRequest(BaseModel):
    email: EmailStr
    source: str = "homepage"


def _send_free_chapter_email(email: str) -> bool:
    """Send free chapter download link via SendGrid. Returns True on success."""
    if not settings.sendgrid_api_key:
        print(f"⚠️ SendGrid not configured — skipping email to {email}")
        return False

    try:
        import sendgrid
        from sendgrid.helpers.mail import Mail, To, From, Subject, HtmlContent

        sg = sendgrid.SendGridAPIClient(api_key=settings.sendgrid_api_key)
        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:24px;">
          <h2 style="color:#1f2937;">Your free chapter is ready!</h2>
          <p style="color:#374151;">Thanks for signing up. Here's your free preview of <strong>Video AI Training Data Mastery</strong>
          — the first 10 pages covering the top AI workflow videos for building training data.</p>
          <p style="margin:28px 0;">
            <a href="{FREE_CHAPTER_URL}"
               style="background:#2563eb;color:#fff;padding:14px 28px;border-radius:6px;
                      text-decoration:none;font-weight:700;font-size:16px;">
              Download Free Chapter →
            </a>
          </p>
          <p style="color:#6b7280;font-size:14px;">
            Want all 19 pages plus structured Q&amp;A pairs, workflow templates, and unlimited video processing?
            <a href="https://videomind.ai/checkout" style="color:#2563eb;">Grab the full guide for $39 →</a>
          </p>
          <hr style="margin:28px 0;border:none;border-top:1px solid #e5e7eb;"/>
          <p style="color:#9ca3af;font-size:12px;">
            You're receiving this because you requested the free chapter at VideoMind AI.
          </p>
        </div>
        """
        message = Mail(
            from_email=From(settings.from_email, "VideoMind AI"),
            to_emails=To(email),
            subject=Subject("Your free chapter: Top AI Workflow Videos for Training Data"),
            html_content=HtmlContent(html),
        )
        resp = sg.send(message)
        return resp.status_code in (200, 202)
    except Exception as e:
        print(f"⚠️ SendGrid send failed: {e}")
        return False


def _send_nurture_email(email: str) -> bool:
    """Send day-2 nurture email with WEEK2 discount code."""
    if not settings.sendgrid_api_key:
        return False

    try:
        import sendgrid
        from sendgrid.helpers.mail import Mail, To, From, Subject, HtmlContent

        sg = sendgrid.SendGridAPIClient(api_key=settings.sendgrid_api_key)
        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:24px;">
          <h2 style="color:#1f2937;">Liked the free chapter?</h2>
          <p style="color:#374151;">
            The full <strong>Video AI Training Data Mastery</strong> guide has everything you need:
            structured Q&amp;A pairs, workflow templates, and step-by-step instructions for turning
            any video into LLM training data.
          </p>
          <p style="color:#374151;">Normally $39 — this week only, get <strong>20% off</strong> with code <strong>WEEK2</strong>.</p>
          <p style="margin:28px 0;">
            <a href="https://videomind.ai/checkout?coupon=WEEK2"
               style="background:#16a34a;color:#fff;padding:14px 28px;border-radius:6px;
                      text-decoration:none;font-weight:700;font-size:16px;">
              Get the full guide — 20% off with WEEK2 →
            </a>
          </p>
          <p style="color:#ef4444;font-size:14px;font-weight:600;">⏰ Expires March 24, 2026</p>
          <hr style="margin:28px 0;border:none;border-top:1px solid #e5e7eb;"/>
          <p style="color:#9ca3af;font-size:12px;">
            You're receiving this because you downloaded the free chapter at VideoMind AI.
          </p>
        </div>
        """
        message = Mail(
            from_email=From(settings.from_email, "VideoMind AI"),
            to_emails=To(email),
            subject=Subject("Liked the free chapter? Get 20% off the full guide (code: WEEK2)"),
            html_content=HtmlContent(html),
        )
        resp = sg.send(message)
        return resp.status_code in (200, 202)
    except Exception as e:
        print(f"⚠️ SendGrid nurture send failed: {e}")
        return False


@router.post("/leads/capture")
async def capture_lead(payload: LeadCaptureRequest, db: Session = Depends(get_database)):
    """Capture email lead and send free chapter download link."""
    email = payload.email.lower().strip()

    # Check for existing lead
    existing = db.query(Lead).filter(Lead.email == email).first()
    if existing:
        if not existing.free_chapter_sent:
            sent = _send_free_chapter_email(email)
            if sent:
                existing.free_chapter_sent = True
                db.commit()
        return {"success": True, "message": "Check your email for the free chapter link!", "new": False}

    # Create lead
    nurture_at = datetime.utcnow() + timedelta(hours=48)
    lead = Lead(
        email=email,
        source=payload.source,
        nurture_scheduled_at=nurture_at,
    )
    db.add(lead)
    try:
        db.commit()
        db.refresh(lead)
    except IntegrityError:
        db.rollback()
        return {"success": True, "message": "Check your email for the free chapter link!", "new": False}

    # Send free chapter
    sent = _send_free_chapter_email(email)
    if sent:
        lead.free_chapter_sent = True
        db.commit()

    return {
        "success": True,
        "message": "Check your email for the free chapter link!",
        "new": True,
        "email_sent": sent,
    }


@router.post("/leads/send-nurture")
async def send_nurture_emails(db: Session = Depends(get_database)):
    """
    Send day-2 nurture emails to leads whose nurture_scheduled_at has passed.
    Intended to be triggered manually or by a cron job.
    """
    now = datetime.utcnow()
    pending = (
        db.query(Lead)
        .filter(
            Lead.nurture_sent == False,  # noqa: E712
            Lead.nurture_scheduled_at <= now,
        )
        .all()
    )

    sent_count = 0
    for lead in pending:
        ok = _send_nurture_email(lead.email)
        if ok:
            lead.nurture_sent = True
            lead.nurture_sent_at = now
            sent_count += 1

    db.commit()
    return {"success": True, "sent": sent_count, "total_pending": len(pending)}


@router.get("/leads/stats")
async def lead_stats(db: Session = Depends(get_database)):
    """Basic stats for the lead list."""
    from sqlalchemy import func
    total = db.query(func.count(Lead.id)).scalar() or 0
    chapter_sent = db.query(func.count(Lead.id)).filter(Lead.free_chapter_sent == True).scalar() or 0  # noqa: E712
    nurtured = db.query(func.count(Lead.id)).filter(Lead.nurture_sent == True).scalar() or 0  # noqa: E712
    return {"total": total, "free_chapter_sent": chapter_sent, "nurtured": nurtured}
