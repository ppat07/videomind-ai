"""Newsletter endpoints (Mailchimp)."""
from __future__ import annotations

import hashlib
from typing import Optional

import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from config import settings

router = APIRouter()


class SubscribeRequest(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None


@router.post("/newsletter/subscribe")
async def subscribe_newsletter(payload: SubscribeRequest):
    if not settings.mailchimp_api_key or not settings.mailchimp_audience_id or not settings.mailchimp_server_prefix:
        raise HTTPException(status_code=500, detail="Mailchimp is not configured")

    dc = settings.mailchimp_server_prefix
    audience_id = settings.mailchimp_audience_id
    tag = settings.mailchimp_tag or "videomind"

    base = f"https://{dc}.api.mailchimp.com/3.0"
    subscriber_hash = hashlib.md5(payload.email.lower().encode("utf-8")).hexdigest()

    member_url = f"{base}/lists/{audience_id}/members/{subscriber_hash}"
    auth = ("anystring", settings.mailchimp_api_key)

    body = {
        "email_address": payload.email,
        "status_if_new": "subscribed",
        "status": "subscribed",
        "merge_fields": {
            "FNAME": payload.first_name or "",
            "LNAME": payload.last_name or "",
        },
    }

    r = requests.put(member_url, auth=auth, json=body, timeout=20)
    if r.status_code not in (200, 201):
        detail = r.json().get("detail", "Mailchimp error") if r.headers.get("content-type", "").startswith("application/json") else r.text
        raise HTTPException(status_code=400, detail=f"Subscribe failed: {detail}")

    # Apply tag
    tags_url = f"{member_url}/tags"
    t = requests.post(tags_url, auth=auth, json={"tags": [{"name": tag, "status": "active"}]}, timeout=20)
    if t.status_code not in (200, 204):
        # Soft fail tagging; subscription itself succeeded
        return {"success": True, "tagged": False, "message": "Subscribed, but tag failed"}

    return {"success": True, "tagged": True, "message": "Subscribed successfully"}
