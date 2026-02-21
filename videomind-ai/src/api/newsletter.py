"""Newsletter endpoints (Mailchimp + weekly digest generation)."""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from typing import Optional

import requests
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from config import settings
from database import get_database
from models.directory import DirectoryEntry

router = APIRouter()


class SubscribeRequest(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class DigestSendRequest(BaseModel):
    subject: Optional[str] = None
    days: int = 7
    limit: int = 8
    send_now: bool = False


def _mailchimp_config_ok() -> bool:
    return bool(settings.mailchimp_api_key and settings.mailchimp_audience_id and settings.mailchimp_server_prefix)


def _mailchimp_base() -> str:
    return f"https://{settings.mailchimp_server_prefix}.api.mailchimp.com/3.0"


def _mailchimp_auth() -> tuple:
    return ("anystring", settings.mailchimp_api_key)


def _top_entries(db: Session, days: int, limit: int):
    since = datetime.utcnow() - timedelta(days=max(1, min(days, 30)))
    return (
        db.query(DirectoryEntry)
        .filter(DirectoryEntry.created_at >= since)
        .order_by(DirectoryEntry.signal_score.desc(), DirectoryEntry.created_at.desc())
        .limit(max(1, min(limit, 20)))
        .all()
    )


def _digest_subject() -> str:
    return f"Weekly AI Workflow Digest — {datetime.utcnow().strftime('%b %d, %Y')}"


def _digest_html(entries) -> str:
    items = []
    for e in entries:
        items.append(
            f"""
            <li style='margin-bottom:14px;'>
              <a href='{e.video_url}' style='font-weight:700;color:#1f2937;text-decoration:none;'>{e.title}</a><br/>
              <span style='color:#6b7280;font-size:13px;'>Creator: {e.creator_name or 'Unknown'} · Signal: {e.signal_score or 0}/100 · {e.category_primary or 'Workflow'}</span><br/>
              <span style='color:#374151;font-size:14px;'>{(e.summary_5_bullets or '').replace('•', '').replace(chr(10), ' ')[:220]}</span>
            </li>
            """.strip()
        )

    if not items:
        items.append("<li>No new high-signal videos this week yet.</li>")

    return f"""
    <div style='font-family:Arial,sans-serif;max-width:680px;margin:0 auto;padding:20px;'>
      <h2 style='margin-bottom:6px;'>Weekly AI Workflow Digest</h2>
      <p style='color:#6b7280;margin-top:0;'>Top workflow videos curated from VideoMind AI.</p>
      <ul style='padding-left:18px;'>
        {''.join(items)}
      </ul>
      <hr style='margin:24px 0;border:none;border-top:1px solid #e5e7eb;' />
      <p style='font-size:12px;color:#9ca3af;'>You're receiving this because you subscribed to VideoMind workflow updates.</p>
    </div>
    """.strip()


@router.post("/newsletter/subscribe")
async def subscribe_newsletter(payload: SubscribeRequest):
    if not _mailchimp_config_ok():
        raise HTTPException(status_code=500, detail="Mailchimp is not configured")

    dc_base = _mailchimp_base()
    audience_id = settings.mailchimp_audience_id
    tag = settings.mailchimp_tag or "videomind"

    subscriber_hash = hashlib.md5(payload.email.lower().encode("utf-8")).hexdigest()
    member_url = f"{dc_base}/lists/{audience_id}/members/{subscriber_hash}"

    body = {
        "email_address": payload.email,
        "status_if_new": "subscribed",
        "status": "subscribed",
        "merge_fields": {
            "FNAME": payload.first_name or "",
            "LNAME": payload.last_name or "",
        },
    }

    r = requests.put(member_url, auth=_mailchimp_auth(), json=body, timeout=20)
    if r.status_code not in (200, 201):
        detail = r.json().get("detail", "Mailchimp error") if r.headers.get("content-type", "").startswith("application/json") else r.text
        raise HTTPException(status_code=400, detail=f"Subscribe failed: {detail}")

    tags_url = f"{member_url}/tags"
    t = requests.post(tags_url, auth=_mailchimp_auth(), json={"tags": [{"name": tag, "status": "active"}]}, timeout=20)
    if t.status_code not in (200, 204):
        return {"success": True, "tagged": False, "message": "Subscribed, but tag failed"}

    return {"success": True, "tagged": True, "message": "Subscribed successfully"}


@router.get("/newsletter/digest/preview")
async def digest_preview(days: int = 7, limit: int = 8, db: Session = Depends(get_database)):
    rows = _top_entries(db, days=days, limit=limit)
    subject = _digest_subject()
    html = _digest_html(rows)
    return {
        "subject": subject,
        "count": len(rows),
        "items": [
            {
                "title": r.title,
                "video_url": r.video_url,
                "creator_name": r.creator_name,
                "signal_score": r.signal_score,
                "category_primary": r.category_primary,
            }
            for r in rows
        ],
        "html": html,
    }


@router.post("/newsletter/digest/send")
async def digest_send(payload: DigestSendRequest, db: Session = Depends(get_database)):
    if not _mailchimp_config_ok():
        raise HTTPException(status_code=500, detail="Mailchimp is not configured")

    rows = _top_entries(db, days=payload.days, limit=payload.limit)
    subject = payload.subject or _digest_subject()
    html = _digest_html(rows)

    base = _mailchimp_base()
    auth = _mailchimp_auth()

    campaign_body = {
        "type": "regular",
        "recipients": {
            "list_id": settings.mailchimp_audience_id,
        },
        "settings": {
            "subject_line": subject,
            "title": f"VideoMind Digest {datetime.utcnow().isoformat()}",
            "from_name": settings.app_name,
            "reply_to": settings.from_email,
        },
    }

    c = requests.post(f"{base}/campaigns", auth=auth, json=campaign_body, timeout=20)
    if c.status_code not in (200, 201):
        detail = c.json().get("detail", "Campaign create failed") if c.headers.get("content-type", "").startswith("application/json") else c.text
        raise HTTPException(status_code=400, detail=detail)

    campaign_id = c.json().get("id")

    content_resp = requests.put(
        f"{base}/campaigns/{campaign_id}/content",
        auth=auth,
        json={"html": html},
        timeout=20,
    )
    if content_resp.status_code not in (200, 204):
        detail = content_resp.json().get("detail", "Campaign content update failed") if content_resp.headers.get("content-type", "").startswith("application/json") else content_resp.text
        raise HTTPException(status_code=400, detail=detail)

    sent = False
    if payload.send_now:
        s = requests.post(f"{base}/campaigns/{campaign_id}/actions/send", auth=auth, timeout=20)
        if s.status_code not in (200, 204):
            detail = s.json().get("detail", "Campaign send failed") if s.headers.get("content-type", "").startswith("application/json") else s.text
            raise HTTPException(status_code=400, detail=detail)
        sent = True

    return {
        "success": True,
        "campaign_id": campaign_id,
        "subject": subject,
        "entries_used": len(rows),
        "sent": sent,
        "note": "By default this targets the configured audience; use Mailchimp segmentation/tag targeting in campaign settings if needed.",
    }
