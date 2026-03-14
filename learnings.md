# learnings.md - One-Liner Rules

*Rules derived from mistakes, decisions, and lessons learned. Checked before every task.*

## VideoMind AI Business Rules
- Never add fake/unverified content to directory - customer trust is everything
- Verify all YouTube URLs resolve before adding to directory
- "Training AI Through Video" positioning > "Replace Video Teams" messaging
- Test → Debug → Fix → Verify → THEN report success (never claim "fixed" without production verification)
- No complexity until real limits - don't add agents/tools preemptively
- Revenue sequence: Info products → Agency → Marketplace → Own product

## Security Rules
- API keys belong in .env, never hardcoded in config files
- After migrating secrets to env vars, delete all backup files (.bak) containing old keys
- Runtime cache files (e.g. models.json) may contain resolved secrets - check and clean them too
- Rotate keys immediately if they've been exposed in logs or chat transcripts
- Skill environment blocks don't support env var interpolation - AgentMail API key must stay literal in openclaw.json, not in .env

## System Prompt & Memory Rules
- Config files and docs must agree - if config says "enabled: false", docs can't say "enabled"
- Count your lists - if you say "Five Pillars", list exactly five
- Delete fully redundant files (IDENTITY.md = SOUL.md duplicate = delete it)
- Don't duplicate AGENTS.md rules here - this file is for lessons, not copies
- keepLastResponses below 5 risks losing mid-task context
- Cross-file redundancy = wasted tokens - audit periodically
- OpenClaw validates config strictly - unsupported fields get stripped on restart. Control behavior through prompt files, not invented config keys.

## Lessons from Mistakes
- Rick Astley as "OpenClaw tutorial" = reputation crisis - always verify content authenticity
- Directory reset during deployments = verify production state after major changes
- Context window overflow = audit system prompt quarterly for bloat
- memoryFlush config vs HEARTBEAT.md contradiction went unnoticed - always cross-check config against docs
- Mixed content types (videos + articles) confuse business positioning - focus on ONE clear value prop
- Directory rebuilds should use pre-verified content lists - prevents fake content contamination
- Never expose internal admin tools to customer-facing websites - use password protection, not removal
- Remove customer-visible links to admin tools - protect access, don't eliminate functionality

---

*Add new rules when mistakes happen. One line per rule. Keep it actionable.*
