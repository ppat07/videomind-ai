"""
Lead capture endpoint: email signup → free training script delivery via SendGrid.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from config import settings
from database import get_database
from models.leads import Lead
from models.directory import DirectoryEntry

router = APIRouter()


class LeadCaptureRequest(BaseModel):
    email: EmailStr
    source: str = "homepage"


def _get_featured_entry(db: Session) -> Optional[DirectoryEntry]:
    """Return the highest-quality directory entry for the free sample email."""
    return (
        db.query(DirectoryEntry)
        .filter(DirectoryEntry.summary_5_bullets.isnot(None))
        .order_by(DirectoryEntry.signal_score.desc())
        .first()
    )


def _format_training_script_html(entry: Optional[DirectoryEntry]) -> str:
    """Render the training script section as inline HTML."""
    if not entry:
        return "<p style='color:#374151;font-style:italic;'>Training script coming soon — check back after you sign up!</p>"

    # Prefer the full agent training script; fall back to summary bullets
    script_text = entry.agent_training_script or entry.summary_5_bullets or ""

    # Convert plain-text bullets to simple HTML paragraphs
    lines = [ln.strip() for ln in script_text.splitlines() if ln.strip()]
    items_html = "".join(
        f"<li style='margin-bottom:8px;color:#374151;'>{ln.lstrip('•- ')}</li>"
        for ln in lines
    )

    video_url = entry.source_url or entry.video_url or "#"
    title = entry.title or "Featured AI Workflow Video"
    creator = entry.creator_name or "Unknown creator"

    return f"""
    <div style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px;padding:20px;margin:24px 0;">
      <p style="margin:0 0 4px;font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:#6b7280;">
        Your Free Training Script
      </p>
      <h3 style="margin:0 0 4px;color:#1f2937;">
        <a href="{video_url}" style="color:#1f2937;text-decoration:none;">{title}</a>
      </h3>
      <p style="margin:0 0 16px;font-size:13px;color:#6b7280;">by {creator}</p>
      <ul style="margin:0;padding-left:20px;">
        {items_html if items_html else "<li>See the full script by clicking the video link above.</li>"}
      </ul>
      <p style="margin:16px 0 0;font-size:13px;color:#6b7280;font-style:italic;">
        This is your free training script. Pro members get all 72.
      </p>
    </div>
    """


def _send_welcome_email(email: str, db: Session) -> bool:
    """Send welcome email with one free training script via SendGrid. Returns True on success."""
    if not settings.sendgrid_api_key:
        print(f"⚠️ SendGrid not configured — skipping email to {email}")
        return False

    try:
        import sendgrid
        from sendgrid.helpers.mail import Mail, To, From, Subject, HtmlContent

        featured = _get_featured_entry(db)
        script_section = _format_training_script_html(featured)

        sg = sendgrid.SendGridAPIClient(api_key=settings.sendgrid_api_key)
        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:24px;">
          <h2 style="color:#1f2937;">Welcome to VideoMind AI!</h2>
          <p style="color:#374151;">
            Thanks for signing up. Here's a complete training script from our library — totally free,
            no strings attached.
          </p>
          {script_section}
          <p style="color:#374151;margin:20px 0 8px;">
            Ready to unlock all 72 training scripts plus unlimited video processing?
          </p>
          <p style="margin:0 0 28px;">
            <a href="https://videomind-ai.com/pricing?coupon=FOUNDING"
               style="background:#2563eb;color:#fff;padding:14px 28px;border-radius:6px;
                      text-decoration:none;font-weight:700;font-size:16px;">
              Get unlimited access — join Pro at $49/mo →
            </a>
          </p>
          <p style="color:#6b7280;font-size:14px;">
            Use code <strong>FOUNDING</strong> at checkout — lock in $29/mo forever.
          </p>
          <hr style="margin:28px 0;border:none;border-top:1px solid #e5e7eb;"/>
          <p style="color:#9ca3af;font-size:12px;">
            You're receiving this because you signed up at VideoMind AI.
          </p>
        </div>
        """
        message = Mail(
            from_email=From(settings.from_email, "VideoMind AI"),
            to_emails=To(email),
            subject=Subject("Your free training script from VideoMind AI"),
            html_content=HtmlContent(html),
        )
        resp = sg.send(message)
        return resp.status_code in (200, 202)
    except Exception as e:
        print(f"⚠️ SendGrid send failed: {e}")
        return False


# Keep old name as an alias so any existing callers don't break
def _send_free_chapter_email(email: str, db: Optional[Session] = None) -> bool:
    """Backwards-compat wrapper — now sends the free training script welcome email."""
    if db is None:
        print(f"⚠️ No db session provided to _send_free_chapter_email — email skipped for {email}")
        return False
    return _send_welcome_email(email, db)


def _send_nurture_email(email: str) -> bool:
    """Send day-2 nurture email with FOUNDING discount code."""
    if not settings.sendgrid_api_key:
        return False

    try:
        import sendgrid
        from sendgrid.helpers.mail import Mail, To, From, Subject, HtmlContent

        sg = sendgrid.SendGridAPIClient(api_key=settings.sendgrid_api_key)
        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:24px;">
          <h2 style="color:#1f2937;">Liked your free training script?</h2>
          <p style="color:#374151;">
            VideoMind AI Pro gives you all 72 training scripts plus unlimited video processing —
            structured Q&amp;A pairs, workflow templates, and step-by-step agent training data
            for every video in our library.
          </p>
          <p style="color:#374151;">
            Join as a Founding Member at <strong>$29/mo forever</strong> (vs $49/mo regular).
            Use code <strong>FOUNDING</strong> at checkout — this rate locks in permanently.
          </p>
          <p style="margin:28px 0;">
            <a href="https://videomind-ai.com/pricing?coupon=FOUNDING"
               style="background:#16a34a;color:#fff;padding:14px 28px;border-radius:6px;
                      text-decoration:none;font-weight:700;font-size:16px;">
              Become a Founding Member — $29/mo forever →
            </a>
          </p>
          <hr style="margin:28px 0;border:none;border-top:1px solid #e5e7eb;"/>
          <p style="color:#9ca3af;font-size:12px;">
            You're receiving this because you signed up at VideoMind AI.
          </p>
        </div>
        """
        message = Mail(
            from_email=From(settings.from_email, "VideoMind AI"),
            to_emails=To(email),
            subject=Subject("Liked your free training script? Become a Founding Member — $29/mo forever"),
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
            sent = _send_welcome_email(email, db)
            if sent:
                existing.free_chapter_sent = True
                db.commit()
        return {"success": True, "message": "Check your email for your free training script!", "new": False}

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
        return {"success": True, "message": "Check your email for your free training script!", "new": False}

    # Send free training script welcome email
    sent = _send_welcome_email(email, db)
    if sent:
        lead.free_chapter_sent = True
        db.commit()

    return {
        "success": True,
        "message": "Check your email for your free training script!",
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
