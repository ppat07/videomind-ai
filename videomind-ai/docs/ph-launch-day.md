# Product Hunt Launch Day — March 31, 2026

> Execute in this exact order. Total time: ~30 minutes active, then monitor all day.

---

## T-1 Day (Sunday March 30)

- [ ] Post teaser on Twitter: "Launching on Product Hunt tomorrow 🚀 VideoMind AI — turn any YouTube video into AI training data. FOUNDING rate ($29/mo forever) expires April 15."
- [ ] DM 10-15 people in your network who would genuinely use this (don't ask for upvotes)
- [ ] Test checkout: `https://videomind-ai.com/checkout?coupon=FOUNDING` — verify coupon auto-applies
- [ ] Test demo: paste `https://www.youtube.com/watch?v=kCc8FmEb1nY` — verify Q&A pairs show up
- [ ] Copy-paste founder comment from `docs/product-hunt-launch.md` into a text file (ready to paste)

---

## T-0: Launch (12:01am PT, Tuesday March 31)

**Submit to Product Hunt:**
1. Go to: `https://www.producthunt.com/posts/new`
2. URL: `https://videomind-ai.com`
3. Name: `VideoMind AI`
4. Tagline: `Turn any AI workflow video into training data` *(46 chars)*
5. Description: Option C from `docs/product-hunt-launch.md`
6. Topics: Artificial Intelligence, Machine Learning, Developer Tools
7. Submit

**Immediately after submission (within 5 min):**
- Post the founder comment from `docs/product-hunt-launch.md` as the first comment

**Share on Twitter:**
```
Just launched on Product Hunt! 🚀

VideoMind AI: turn any YouTube video into structured LLM training data.

72 pre-processed AI/ML videos (Karpathy, 3Blue1Brown, more) — free to browse.

FOUNDING rate: $29/mo forever, expires April 15.

[PH link] | videomind-ai.com
```

---

## Launch Day (8am–10pm PT) — Response Strategy

- [ ] Check PH every 30 minutes
- [ ] Reply to EVERY comment within 1 hour — even "Thanks!" counts for algorithm
- [ ] If someone asks a technical question, give a detailed answer (shows depth)
- [ ] If someone says "this is cool" — ask what they'd use it for (engagement + insight)
- [ ] Post a PH comment update at 12 hours: "6 hours in — here's what we've learned..."

**Common questions to prepare for:**
- "How is this different from Whisper?" → We do more than transcription: structured Q&A pairs, agent training scripts, topic tags, quality scoring
- "Is this free?" → Free tier: 3 videos/day. Pro: $29/mo (FOUNDING), unlimited processing
- "What about copyright?" → We process transcripts from auto-captions/captions, same as any transcript tool

---

## Post-Launch (April 1+)

- Reply to late PH comments (many come in Day 2–3)
- Post a launch day recap on Twitter: "We launched on PH yesterday — here's what happened"
- Follow up with anyone who commented but didn't try the product
- Email any leads captured during launch day with a "Thanks for checking us out" note

---

## Key URLs for Launch Day

| Page | URL |
|------|-----|
| Direct checkout (FOUNDING pre-applied) | `videomind-ai.com/checkout?coupon=FOUNDING` |
| Directory | `videomind-ai.com/directory` |
| Karpathy GPT page | `videomind-ai.com/training/397b2584-1051-5e56-8632-ed76347aec1e` |
| Admin health | `videomind-ai.com/api/admin/health` (basic auth) |
| **Funnel metrics (24h/7d)** | **`videomind-ai.com/api/admin/funnel` (basic auth)** |

---

## ⚠️ Pre-Launch: Protect Lead Data (Optional but Recommended)

**Problem:** Render free tier uses ephemeral disk — SQLite resets on every cold start, wiping captured leads and nurture schedules. Pro subscriber access is protected (Stripe sync runs on startup), but email leads are not.

**Quick fix before March 31 (~5 min):**
1. In Render dashboard → your service → **Disks** → Add Disk
   - Name: `videomind-db`
   - Mount Path: `/data`
   - Size: 1 GB (costs ~$0.25/mo on paid plan, or free on Starter disk)
2. Add env var in Render: `DATABASE_URL=sqlite:////data/videomind.db`
3. Redeploy — SQLite will now persist across restarts

**If you skip this:** Welcome emails still fire immediately on lead capture, so leads get contacted. But the 48hr nurture email sequence won't run for leads captured before a restart.

---

*Ready to launch. The product works. The funnel is tight. Go get those subscribers.*
