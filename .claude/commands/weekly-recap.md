# /weekly-recap — Weekly Summary

Generate a comprehensive weekly summary across all tools and data sources.

## Instructions

Run these in sequence (calendar and Slack first, then email per rate-limit rule):

### 1. Calendar Review
- Use `mcp__google-workspace__get_events` for the past 7 days:
  - `user_google_email: "philip.bornhurst@doordash.com"`
- Count: total meetings, mx calls, internal meetings
- List mx calls with brief outcome if notes available

### 2. Slack Activity
- Use `mcp__slack__slack_search_public_and_private` for Phil's mentions this week
- Use `mcp__slack__slack_read_channel` on #pathfinder-support (C067SSZ1AMT) for the week's escalations
- Summarize key threads and outcomes

### 3. Email Summary
- Use `mcp__google-workspace__search_gmail_messages`:
  - `user_google_email: "philip.bornhurst@doordash.com"`
  - `query: "after:YYYY/MM/DD before:YYYY/MM/DD"`
- Count total, highlight important threads

### 4. Volume Trends
- Read Volume Drop Data spreadsheet (same as /volume-alert):
  - `spreadsheet_id: "1bu0fWwKWQQeI8nrkhGKA68dTzKRtIh_MXAPeqze0NX0"`
  - `user_google_email: "philip.bornhurst@doordash.com"`
- Compare this week vs last week
- Flag any new gone-dark mx

### 5. Product Feedback
- Read Product Feedback Tracker for entries added this week:
  - `spreadsheet_id: "1-EylRCLxhpStfEoj-8ga9Ex_26dHBoWgxU6Yr_hT0Y4"`
  - `range_name: "The Final Final Boss"`
  - `user_google_email: "philip.bornhurst@doordash.com"`
- Count new entries, summarize themes

### 6. Compile

```
## Weekly Recap: [date range]

### By the Numbers
- Meetings: X total (Y mx calls, Z internal)
- Emails: X received, Y sent
- Support escalations: X (Y resolved)
- Volume alerts: X new drops
- Feedback logged: X new entries

### Merchant Highlights
- [mx name] — notable event (call, escalation, volume change)
- ...

### Wins
- [positive outcomes this week]

### Open Items
- [ ] Things that still need attention
- ...

### Next Week Preview
- [upcoming mx calls from calendar]
- [pending follow-ups]
```

## Example usage

```
/weekly-recap
/weekly-recap last 2 weeks
/weekly-recap Mallory's accounts only
```
