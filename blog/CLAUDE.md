# Restaurant Tech Speaking Practice

Personal practice tool for becoming a sharper, more confident speaker on restaurant technology topics. Not for publication — this is about building the muscle to talk endlessly about a subject while keeping points sharp.

---

## About

- **Who:** Philip Bornhurst — Head of Account Management, Pathfinder (DoorDash's POS product)
- **Email:** philip.bornhurst@doordash.com
- **Goal:** Practice speaking about restaurant tech to improve meeting presence and general communication

---

## How It Works

1. `/topic` — Get a speaking topic with prep notes and framework
2. Record yourself speaking (1, 3, or 5 minutes)
3. `/review ~/path/to/recording.m4a` — Get scored feedback on the recording
4. `/progress` — Track improvement over time

---

## Commands

| Command | Purpose |
|---------|---------|
| `/topic` | Pick a restaurant tech speaking topic with prep notes |
| `/review` | Analyze a speaking recording with structured feedback and scoring |
| `/progress` | Show speaking practice progress, trends, and recommendations |

---

## Project Structure

```
blog/
  CLAUDE.md           — This file
  README.md           — Project overview
  rubric.md           — 5-dimension scoring rubric
  topics/             — Topic library (6 category files, ~20 topics)
  .claude/commands/   — Slash commands (topic, review, progress)
```

---

## Scoring Rubric

5 dimensions, scored 1-5 each (25 total). Full details in `rubric.md`.

1. **Content & Structure** — thesis, flow, transitions, evidence, conclusion
2. **Delivery & Pace** — natural pace, pauses, speed variation, energy
3. **Clarity & Filler Words** — filler count, articulation, restarted sentences
4. **Persuasiveness & Confidence** — authority, evidence-backed, conviction
5. **Engagement & Relatability** — stories, analogies, concrete examples

**Bands:** 21-25 Excellent | 16-20 Strong | 11-15 Developing | 6-10 Early | 1-5 Starting

---

## Topic Categories

| Code | Category |
|------|----------|
| POS | POS Fundamentals |
| OPS | Restaurant Operations |
| DD | DoorDash Platform |
| IND | Industry Trends |
| PF | Pathfinder Deep Dives |
| SAL | Sales & Partnerships |

---

## Progress Tracking

Sessions are logged to a Google Sheet (created on first `/review`).

**Spreadsheet ID:** _(populated after first session)_

---

## Rules

1. **google-workspace email** — ALWAYS pass `user_google_email: "philip.bornhurst@doordash.com"` to every google-workspace tool call.
2. **Confirm before writing** — Never modify the tracking sheet without showing the data and getting explicit confirmation.
3. **Be direct** — Feedback should be honest and specific. This is for self-improvement, not ego.
4. **Use Gemini for recordings** — Analyze audio/video via `mcp__gemini__gemini-analyze-document`. Layer Claude's scoring and comparison on top.
