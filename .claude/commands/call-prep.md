# /call-prep — Call Preparation

Prepare a comprehensive brief for a merchant call.

## Instructions

1. **Identify the call:**
   - If a mx name/ID is provided, use that directly.
   - If no mx specified, check today's calendar using `mcp__claude_ai_Google_Calendar__list_events`.
   - Identify the next mx call and extract the mx name from the event.

2. **Run a full mx-lookup** (follow mx-lookup skill instructions):
   - Master Hub data (tier, status, MSAT, AM, notes link)
   - Volume Drop Data (current/previous volume, trend)
   - Intercom conversations (primary support — all mx inbound texts)
   - Slack mentions in #pathfinder-support (escalations only — critical subset)
   - Snowflake data via POS Cohort Query (see CLAUDE.md Key Data Tables) — Lifetime OSW, GOV/week, AOV, lifecycle dates, activation status

3. **Pull additional context:**

   a. **Recent emails** — Use `mcp__claude_ai_Gmail__search_threads`:
      - `query`: mx name or contact email
      - Summarize last 3-5 exchanges

   b. **Product Feedback** — Use `gws sheets +read --spreadsheet 1-EylRCLxhpStfEoj-8ga9Ex_26dHBoWgxU6Yr_hT0Y4 --range "The Final Final Boss"`:
      - Filter for this mx's feedback entries

   c. **Intercom tickets** (primary support channel) — Use `mcp__intercom__search_conversations` to search for recent conversations mentioning this mx:
      - Search by mx name or contact email
      - If contact isn't clearly identifiable, use `mcp__intercom__get_contact` and cross-reference against Master Hub by business name, phone, or email
      - Summarize any open/recent tickets — this is where most support activity lives

   d. **Running notes doc** — If a notes link is in Master Hub, read it with `gws docs documents get --params '{"documentId":"DOC_ID","includeTabsContent":true}'` (or `mcp__claude_ai_Google_Drive__read_file_content`).

4. **Compile into call prep brief:**

```
## Call Prep: [Merchant Name]
**Date/Time:** [from calendar] | **Type:** Check-in / QBR / Intro
**Store ID:** XXXXX | **Tier:** ICP | **AM:** Phil
**Portal:** https://www.doordash.com/merchant/sales?store_id=XXXXX

### Quick Stats
- **Lifetime OSW:** X orders/week | **Lifetime GOV/Week:** $X
- **Volume:** X orders/week (trend) | **AOV:** $X
- **MSAT:** X/5
- **Status:** Live since [date]
- **Lifecycle:** CW [date] → OB [date] → Install [date] → Go-Active [date]

### Recent Activity
- Last email: [date] — subject/summary
- Last Slack escalation: [date] — issue/resolution
- Last Intercom ticket: [date] — issue/status
- Last volume change: [date] — details

### Open Product Feedback
- Feature request 1 (status)
- Bug report 2 (status)

### Talking Points
1. [Auto-generated based on data — volume trends, open issues, upsell opportunities]
2. ...

### Running Notes Summary
[Key points from Google Doc]
```

## Example usage

```
/call-prep Taco Bell
/call-prep Store 12345
/call-prep
```

The last one auto-detects the next mx call from today's calendar.
