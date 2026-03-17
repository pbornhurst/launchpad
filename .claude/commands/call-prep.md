# /call-prep — Call Preparation

Prepare a comprehensive brief for a merchant call.

## Instructions

1. **Identify the call:**
   - If a mx name/ID is provided, use that directly.
   - If no mx specified, check today's calendar using `mcp__google-workspace__get_events`:
     - `user_google_email: "philip.bornhurst@doordash.com"`
   - Identify the next mx call and extract the mx name from the event.

2. **Run a full mx-lookup** (follow mx-lookup skill instructions):
   - Master Hub data (tier, status, MSAT, AM, notes link)
   - Volume Drop Data (current/previous volume, trend)
   - Slack mentions in #pathfinder-support
   - Snowflake data if Store ID is known

3. **Pull additional context:**

   a. **Recent emails** — Use `mcp__google-workspace__search_gmail_messages`:
      - `user_google_email: "philip.bornhurst@doordash.com"`
      - `query`: mx name or contact email
      - Summarize last 3-5 exchanges

   b. **Product Feedback** — Use `mcp__google-workspace__read_sheet_values`:
      - `spreadsheet_id: "1-EylRCLxhpStfEoj-8ga9Ex_26dHBoWgxU6Yr_hT0Y4"`
      - `range_name: "The Final Final Boss"`
      - `user_google_email: "philip.bornhurst@doordash.com"`
      - Filter for this mx's feedback entries

   c. **Running notes doc** — If a notes link is in Master Hub, use `mcp__google-workspace__get_doc_as_markdown` to read it:
      - `user_google_email: "philip.bornhurst@doordash.com"`

4. **Compile into call prep brief:**

```
## Call Prep: [Merchant Name]
**Date/Time:** [from calendar] | **Type:** Check-in / QBR / Intro
**Store ID:** XXXXX | **Tier:** ICP | **AM:** Phil
**Portal:** https://www.doordash.com/merchant/sales?store_id=XXXXX

### Quick Stats
- Volume: X orders/week (trend)
- MSAT: X/5
- Status: Live since [date]

### Recent Activity
- Last email: [date] — subject/summary
- Last support ticket: [date] — issue/resolution
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
