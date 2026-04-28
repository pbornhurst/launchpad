# /mx-tier — Automated Merchant Tiering

Run the 2026 Mx Journey Health Gate + Tier Scorecard for a single mx. Dispatches 4 parallel sub-agents (support, onboarding, running notes, Snowflake metrics) to gather objective inputs, proposes scores for all 10 scorecard fields, asks Phil to confirm the subjective ones, then writes the scores directly into the `Merchant Health & Tier` tab of the mx's individual file. Posts a summary to #phils-gumloop-agent when finished.

## Usage

```
/mx-tier 12345
/mx-tier Store 12345
/mx-tier Pizza Palace
```

## Instructions

1. Parse `$ARGUMENTS` for a Store ID (numeric) or business name. If empty, ask Phil which mx.
2. Dispatch the `mx-tier` agent with the store identifier.
3. The agent handles Master Hub lookup, mx file resolution, sub-agent fan-out, Phil's subjective confirms, cell writes, and the Slack summary.

## Rubric reference

**Health Scorecard (G7 = weighted avg, graduation ≥ 3.5):**
- G2 Support Inbound Volume (25%) · G3 Issue Status (30%) · G4 Onboarding Satisfaction (15%) · G5 Check-in Attendance (5%) · G6 Overall Mx Sentiment (25%)

**Tier Scorecard (M7 = weighted avg):**
- M2 Weekly GOV (40%) · M3 2026 Segment (30%) · M4 Multi-location (20%) · M5 Mx Feedback (10%) · M6 Is ICP? (override to Tier S)

**Tier output:**
- ICP → Tier S
- Critical Blocker = TRUE OR G7 < 3.5 → Purgatory
- M7 ≥ 3.5 → Tier 1 · 2.5–3.49 → Tier 2 · < 2.5 → Tier 3
