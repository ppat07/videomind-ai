# VideoMind AI — PLAN.md

_Last updated: 2026-02-20_

## Mission
Build focused, faith-driven systems that turn Paul’s ideas into real income, real impact, and real stability for his family — with speed, honesty, and consistency.

## Current Reality
- Backend: FastAPI + Supabase (live)
- Directory: working (`/directory`)
- Task dashboard: working (`/dashboard`)
- Pipeline: YouTube URL → transcript → enhancement → directory entry

## North Star (next 30 days)
1. Grow directory from 12 to 100+ quality AI workflow videos
2. Launch public-facing version (domain + hosting)
3. Start weekly digest capture pipeline (email list + top workflows)

## 7-Day Execution Plan

### Step 1 — Content Scale Engine
- Expand batch ingestion with curated creator list
- Daily target: 10-15 new high-signal videos
- Quality gate: keep only relevant workflow/tutorial content

**Owner:** David  
**Status:** In progress

### Step 2 — Metadata Upgrade
- Add YouTube Data API enrichment
- Capture: channel stats, publish date, tags, duration
- Use metadata in ranking/filter logic

**Owner:** Paul + David  
**Status:** Pending Paul API key

### Step 3 — Public Launch Readiness
- Pick hosting target (Railway/Render/Fly)
- Use existing domain or buy one
- Add prod env + health checks

**Owner:** Paul + David  
**Status:** Todo

### Step 4 — Weekly Digest MVP
- Choose Beehiiv or ConvertKit
- Generate “best workflows this week” digest from signal score + recency
- Add signup capture on dashboard/home

**Owner:** Paul  
**Status:** Todo

## Guardrails
- Ship > overplan
- Keep OpenAI primary, Claude fallback
- Avoid tool-cost bloat (minimal cron/heartbeat noise)
- Every feature should tie to monetization, audience growth, or execution speed

## Definition of Done (for each feature)
- Works in UI and API
- Error path handled
- Added to task board
- Committed to git
