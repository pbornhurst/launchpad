# /support-scan — Combined Support Scanner

Scan both support channels for recent activity: Slack escalations + Intercom inbounds.

> **Channel hierarchy:** Slack #pathfinder-support contains escalated issues (critical, novel, internally-raised). Intercom contains ALL mx inbound support texts. This scan covers both.

## Instructions

### Step 1: Slack Escalations (priority)

1. Read recent messages from #pathfinder-support using `mcp__slack__slack_read_channel`:
   - Channel ID: C067SSZ1AMT
   - Default: last 24 hours. User can specify a different window.
   - **CRITICAL:** The `oldest` and `latest` parameters MUST be **Unix epoch timestamps** (integer seconds since Jan 1, 1970), NOT date strings. Passing `"2026-02-14"` will silently return messages from 2023. Compute the timestamp first (e.g., use Python: `int(datetime(2026,2,14).timestamp())`).
   - **Read the FULL thread** for each message — not just the top-level post. Thread replies contain troubleshooting steps, root cause analysis, and resolution details.
2. Categorize messages:
   - **Escalations** — Messages tagged urgent, mentioning Phil/Mallory, or requesting AM help
   - **New Issues** — Bug reports, outage reports, mx complaints
   - **Resolved** — Issues marked resolved or with resolution messages
   - **Informational** — General updates, announcements
3. For each escalation, try to identify the merchant:
   - Search for Store ID or mx name in the message and thread replies
   - Cross-reference with Master Hub if found

### Step 2: Intercom Inbounds

1. Search recent conversations using `mcp__intercom__search_conversations`:
   - Same time window as Slack scan (default: last 24 hours)
   - For each conversation, use `mcp__intercom__get_conversation` to read the full thread
2. **Triage each conversation** — classify as `support_issue`, `inquiry`, `phone_log`, `greeting_only`, or `noise` based on the full thread content. Only count `support_issue` and `inquiry` as valid inbounds.
3. **Extract the ORIGINAL issue** for valid inbounds — summarize from the mx's first substantive messages, not the latest reply.
4. **Identify the mx** for each valid inbound:
   a. Check the contact's company/business name
   b. If unclear, use `mcp__intercom__get_contact` for full contact details
   c. Cross-reference against Master Hub (`mcp__google-workspace__read_sheet_values`):
      - `spreadsheet_id: "1ndVs2lPhS5frpkEV0KzK7ec5aS18fmr9h1BQEu099E4"`
      - `user_google_email: "philip.bornhurst@doordash.com"`
      - Search by business name, contact name, phone, or email
   d. If matched, include Store ID and tier
5. Highlight notable tickets: ICP/T1 mx, Phil/Mallory's accounts, repeat contacts, urgent themes

### Step 3: Cross-Reference

- If an Intercom ticket matches a Slack escalation (same mx, same issue), link them together
- Note which Intercom tickets have been escalated to Slack vs. which haven't
- **SIT integration:** Both Slack escalations and Intercom inbounds are now logged to the Support Intelligence Tracker (if it exists). Cross-references here feed into the `escalated_repeat` pattern alert — mx with both Slack escalation(s) AND Intercom inbound(s) in the same 7-day window get flagged as HIGH severity.

### Step 4: Pattern Alerts (from Support Intelligence Tracker)

If the SIT spreadsheet exists (check CLAUDE.md Key Spreadsheets for "Support Intelligence Tracker"):
- Read "Pattern Alerts" tab — filter for Status = "new"
- Read "Contact Frequency" tab — filter for Risk Flag = "yes"
- Include in the output below
- If SIT doesn't exist yet, skip this step (no error)

### Step 5: Present

```
## Support Scan — [period]

### Slack Escalations (#pathfinder-support)
**Messages:** N | **Needing response:** X

#### Escalations Needing Response (X)
- **[mx name / Store ID]** — Issue summary (posted by @user, X hours ago) — NEEDS RESPONSE

#### New Issues (N)
- Issue summary (posted by @user, X hours ago)

#### Recently Resolved (N)
- Issue summary — resolved by @user

---

### Intercom Inbounds
**Valid inbounds:** N | **Open:** X | **Closed:** Y
(Excluded: Z phone logs/greetings/noise)

#### Open / Needs Response (X)
- **[mx name]** (Store ID: XXXXX, Tier: ICP) — Issue summary (conv ID, opened X hours ago)
- **[Contact name]** (unmatched) — Issue summary (conv ID, opened X hours ago)

#### Notable Closed (highlights only)
- **[mx name]** — Issue summary (closed X hours ago)

#### Cross-Referenced
- **[mx name]** — Intercom ticket + Slack escalation (linked)

---

### Pattern Alerts (from Support Intelligence Tracker)
If the SIT spreadsheet exists (check CLAUDE.md Key Spreadsheets):
- Read "Pattern Alerts" tab (Status = "new") and "Contact Frequency" tab (Risk Flag = "yes")
- **REPEAT CONTACT** [HIGH] — **Pizza Palace** (Store 12345) — 5 inbounds in 12 days
- **CROSS-MX ISSUE** [MEDIUM] — "POS sync" reported by 3 mx this week
(If no SIT or no alerts: "No active pattern alerts.")

---

### Summary
- **Slack:** X escalations needing response, Y new issues, Z resolved
- **Intercom:** A valid inbounds, B open/unresolved (C noise excluded)
- **Patterns:** X active alerts, Y risk-flagged contacts
- **Highest priority:** [describe top item across both channels]
- **Action needed:** [specific next steps]
```

## Example usage

```
/support-scan
/support-scan last 3 days
/support-scan mentioning kiosk
```
