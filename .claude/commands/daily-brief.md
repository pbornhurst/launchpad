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

### 4. Slack Escalations
- Use `mcp__slack__slack_read_channel` on #pathfinder-support (C067SSZ1AMT)
- Scan last 24 hours for escalations mentioning Phil's mx
- **CRITICAL:** The `oldest` and `latest` parameters MUST be **Unix epoch timestamps** (integer seconds since Jan 1, 1970), NOT date strings. Compute the timestamp first (e.g., for 24h ago: `int((datetime.now() - timedelta(days=1)).timestamp())`).
- Flag anything needing response

### 5. Intercom Inbounds
- Use `mcp__intercom__search_conversations` for last 24 hours
- For each conversation, use `mcp__intercom__get_conversation` to read the full thread
- **Triage**: classify each as `support_issue`, `inquiry`, `phone_log`, `greeting_only`, or `noise` based on the full thread content
- Only count `support_issue` and `inquiry` as valid inbounds. Exclude phone logs, greetings, and noise from counts.
- For valid inbounds, extract the ORIGINAL issue from the mx's first substantive messages (not the latest reply)
- Identify the mx for each valid inbound:
  - Check contact's company/business name
  - If unclear, use `mcp__intercom__get_contact` for full details
  - Cross-reference against Master Hub by business name, phone, or email
- Highlight notable tickets: ICP/T1 mx, Phil/Mallory's accounts, repeat contacts, urgent themes
- Keep it concise — counts + top highlights, not every ticket

### 6. Pattern Alerts (from Support Intelligence Tracker)
- If the SIT spreadsheet exists (check CLAUDE.md Key Spreadsheets for "Support Intelligence Tracker"):
  - Read "Pattern Alerts" tab — filter for Status = "new"
  - Read "Contact Frequency" tab — filter for Risk Flag = "yes"
  - Include in the briefing output below
- If SIT doesn't exist yet, skip this step (no error)

### 7. Compile

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

## Support
### Escalations (#pathfinder-support)
- **[mx name / Store ID]** — Issue summary (posted by @user, X hours ago) — NEEDS RESPONSE
- ...

### Intercom Inbounds (N valid inbounds, X open)
- **[mx name]** (ICP) — Issue summary (open, X hours ago) — NOTABLE
- **[mx name]** — Issue summary (closed)
- + N more routine tickets
(Excluded: Y phone logs/greetings/noise)

### Pattern Alerts (from Support Intelligence Tracker)
- **REPEAT CONTACT** — Pizza Palace: 5 inbounds in 12 days [HIGH]
- **CROSS-MX ISSUE** — POS sync failures across 3 mx [MEDIUM]
(If no SIT or no alerts: "No active pattern alerts.")

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
