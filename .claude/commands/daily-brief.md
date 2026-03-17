# /daily-brief — Morning Briefing

Get a consolidated morning briefing: volume alerts, calendar, Slack, email, and action items.

## Instructions

Run these in order (calendar before email per rate-limit rule):

### 1. Volume Alerts (highest priority)
- Use `mcp__google-workspace__read_sheet_values` on the Volume Drop Data spreadsheet:
  - `spreadsheet_id: "1bu0fWwKWQQeI8nrkhGKA68dTzKRtIh_MXAPeqze0NX0"`
  - `user_google_email: "philip.bornhurst@doordash.com"`
- Flag mx where previous volume > 0 and current volume = 0 or null
- For each flagged mx, include Store ID and merchant portal link

### 2. Calendar
- Use `mcp__google-workspace__get_events`:
  - `user_google_email: "philip.bornhurst@doordash.com"`
  - `time_min`: today start, `time_max`: today end
- List meetings chronologically with time, title, duration, attendees
- Flag first meeting and any mx calls needing prep

### 3. Email
- Use `mcp__google-workspace__search_gmail_messages`:
  - `user_google_email: "philip.bornhurst@doordash.com"`
  - `query: "is:unread"`
- Summarize top 5-10 most important unread messages
- Flag anything urgent or time-sensitive

### 4. Support
- Use `mcp__slack__slack_read_channel` on #pathfinder-support (C067SSZ1AMT)
- Scan last 24 hours for escalations mentioning Phil's mx
- Flag anything needing response

### 5. Compile

Present in this format:

```
## Volume Alerts
- [STORE_ID] Merchant Name — went dark (was X orders/week, now 0) [portal link]

## Today's Schedule (PST)
- 9:00 AM — Meeting Title (30 min) with attendees
- ...

## Email (N unread)
- [Urgent] Subject from sender — summary
- ...

## Support Escalations
- #pathfinder-support: mx issue summary
- ...

## Action Items
- [ ] Respond to X
- [ ] Prep for Y call
- [ ] Follow up on Z
```

## State management

On first run, ask which Slack channels matter beyond #pathfinder-support. Remember for future runs.

## Example usage

```
/daily-brief
/daily-brief include #cx-economics channel
```
