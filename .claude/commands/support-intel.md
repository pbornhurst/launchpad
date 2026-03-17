# /support-intel — Support Intelligence & Pattern Detection

Analyze Intercom conversations and Slack escalations for patterns: repeat inbounders, cross-mx issues, sentiment risk, resolution gaps, escalated repeats. Persistent tracking via the Support Intelligence Tracker (SIT) spreadsheet.

> This command builds institutional memory across sessions. Each scan logs conversations and detects patterns that compound over time.

## Instructions

**Determine mode from input:**
- No args → **Scan mode** (quick daily check, last 48h)
- "deep dive" or a time window (e.g., "30 days") → **Deep dive mode**
- "status" → **Status mode** (read-only, show current alerts)

---

### First-Run Setup

Before any mode, check if the SIT spreadsheet exists:
1. Look for "Support Intelligence Tracker" in CLAUDE.md under Key Spreadsheets
2. If found, use that spreadsheet_id
3. If NOT found:
   a. Create a "support intelligence" subfolder under the 2026 folder using Drive tools:
      - Parent folder ID: `1xPRPSJUWBtJDbeISgOxJiTX0Y8znczf_` (2026)
      - `user_google_email: "philip.bornhurst@doordash.com"`
   b. Create a new Google Sheet in that subfolder:
      - Title: "Support Intelligence Tracker"
      - `user_google_email: "philip.bornhurst@doordash.com"`
   c. Set up 3 tabs with headers:

   **Tab: "Conversation Log"** — Row 1 headers:
   `Conv ID | Source | Date | Contact Name | Contact Email | Contact Phone | Mx Name | Store ID | Tier | Match Key | Conv Type | Message Count | Issue Category | Issue Summary | Thread Context | Sentiment | Status | Escalated | Logged Date`

   **Tab: "Pattern Alerts"** — Row 1 headers:
   `Alert Date | Alert Type | Mx Name | Store ID | Details | Evidence | Severity | Status`

   **Tab: "Contact Frequency"** — Row 1 headers:
   `Contact Key | Contact Name | Contact Email | Contact Phone | Mx Name | Store ID | Tier | Match Status | Total 7d | Total 30d | Total 90d | Last Contact | Top Issues | Risk Flag | Last Updated`

   d. Tell Phil: "Created Support Intelligence Tracker in 2026/support intelligence/. Add this spreadsheet ID to CLAUDE.md under Key Spreadsheets: [ID]. Also add the folder ID to Key Folders."
   e. Proceed with the scan

**SIT spreadsheet_id** — read from CLAUDE.md Key Spreadsheets table (row: "Support Intelligence Tracker"). Always pass `user_google_email: "philip.bornhurst@doordash.com"`.

---

### Scan Mode (default)

Quick daily pattern check. Default window: last 48 hours.

**Step 1: Read existing tracker data**
- Read "Pattern Alerts" tab — filter for Status = "new" (unresolved alerts)
- Read "Contact Frequency" tab — note any contacts with Risk Flag = "yes"
- Read "Conversation Log" tab — get existing Conv IDs (for dedup)

**Step 2: Pull new Intercom conversations**
- Use `mcp__intercom__search_conversations` for last 48 hours (or user-specified window)
- Filter out conversations whose Conv ID already exists in the Conversation Log (dedup)

**Step 2b: Pull Slack escalations**
- Use `mcp__slack__slack_read_channel` on #pathfinder-support (C067SSZ1AMT) for the same time window
- **CRITICAL:** The `oldest` and `latest` parameters MUST be **Unix epoch timestamps** (integer seconds since Jan 1, 1970), NOT date strings. Passing `"2026-02-14"` will silently return messages from 2023. Compute the timestamp first (e.g., use Python: `int(datetime(2026,2,14).timestamp())` → `1771056000`).
- Filter out messages whose Conv ID (`slack_[message_timestamp]`) already exists in the Conversation Log (dedup)
- For each new escalation message:
  - **Read the FULL Slack thread** — read the original message AND all thread replies. Thread replies often contain troubleshooting steps, root cause analysis, and resolution details.
  - Conv ID = `slack_[message_timestamp]`, Source = `slack`
  - Conv Type = `slack_escalation`
  - Extract mx info from the full thread (Store IDs, mx names, phone numbers — may appear in replies, not just the original message)
  - Cross-reference against Master Hub (`spreadsheet_id: "1ndVs2lPhS5frpkEV0KzK7ec5aS18fmr9h1BQEu099E4"`, `user_google_email: "philip.bornhurst@doordash.com"`)
  - Issue Summary = concise 1-2 sentence summary of the escalated issue from the original message
  - Thread Context = condensed notes from thread replies: what was tried, root cause if identified, resolution status, who was involved
  - Classify issue category from content: `payment | menu | orders | POS/technical | onboarding | feature_request | account | general`
  - Assess sentiment/severity from tone and urgency described (1-5 scale)
  - Status = open (unless thread shows resolution)
  - Contact Name = the Slack poster (who escalated), Contact Email/Phone = blank
  - Message Count = thread reply count
  - `slack_escalation` always counts as a valid inbound for pattern detection

**Step 3: Triage and process each new Intercom conversation**

For each Intercom conversation (Source = `intercom`):

a. **Read the FULL conversation thread** — ALWAYS use `mcp__intercom__get_conversation` to pull ALL conversation parts. Do NOT classify from metadata, subject line, or the latest message alone. The original problem is often in the FIRST messages — the latest may just be "Thanks!" or "It worked."

b. **Count messages** — Note the total message count from the mx (not system/admin messages).

c. **Extract the ORIGINAL issue** — Scan the full thread chronologically:
   - Find the mx's FIRST substantive message(s) that describe the problem or question
   - Ignore greetings ("Hello", "Good morning") — look past them for the actual content
   - If the conversation progresses to resolution, note that too
   - The Issue Summary MUST describe the ORIGINAL problem, not the latest reply
   - Example thread: "Hi" → "My POS terminal stopped syncing orders yesterday" → [admin replies] → "It worked. Thank you."
     → Issue Summary = "POS terminal stopped syncing orders" — NOT "It worked. Thank you."
     → Status = closed (resolution confirmed)

d. **Triage: Classify conversation type** — Based on the FULL thread:
   - `support_issue` — mx describes an actual problem needing resolution. **This includes conversations ending with "It worked. Thank you."** — the issue is real, just resolved. Capture the problem, not the thank-you.
   - `inquiry` — mx asking a question (how do I do X, what's the status of Z, can I change Y)
   - `phone_log` — Intercom auto-logged an inbound call with no/minimal text. If notes/transcript exist, reclassify based on content.
   - `greeting_only` — ONLY greetings with no substantive follow-up in the thread (mx said "Hello" and never returned)
   - `noise` — spam, test messages, accidental sends, auto-generated entries with no human content

e. **If Conv Type is `support_issue` or `inquiry`** (VALID INBOUND):
   - **Identify the mx** — contact identification cascade:
     1. Check company/business name from conversation metadata
     2. If unclear, `mcp__intercom__get_contact` for full details (name, email, phone, custom attributes)
     3. Cross-reference against Master Hub (`spreadsheet_id: "1ndVs2lPhS5frpkEV0KzK7ec5aS18fmr9h1BQEu099E4"`, `user_google_email: "philip.bornhurst@doordash.com"`): business name → phone → email → contact name
     4. If matched: populate Mx Name, Store ID, Tier, Match Key
     5. If unmatched: Mx Name = "unmatched", still record all contact info. Do not skip or error.
   - **Write a real issue summary** — 1-2 sentences describing the mx's actual PROBLEM from their messages. Examples:
     - GOOD: "POS terminal at Main St location not syncing orders since Monday. Tried rebooting twice."
     - GOOD: "Menu items showing wrong prices on DoorDash app after recent update — resolved"
     - BAD: "POS/technical" (that's a category, not a summary)
     - BAD: "It worked. Thank you." (that's a reply, not the issue)
     - BAD: "Inbound phone call" (that's metadata, not the issue)
   - **Classify issue category**: `payment | menu | orders | POS/technical | onboarding | feature_request | account | general`
   - **Extract Thread Context** — Condensed notes from the full conversation beyond the Issue Summary: troubleshooting steps taken, workarounds provided, internal agent notes, resolution details. Not a transcript — just the actionable highlights that enrich the intelligence.
   - **Assess sentiment** — Based on the mx's tone DURING the issue, not the resolution thank-you:
     1 = positive/grateful, 2 = neutral, 3 = mildly frustrated, 4 = frustrated/urgent, 5 = angry/churn risk
   - **Check status** — open / closed / snoozed. If conversation ends with resolution confirmation, mark closed.

f. **If Conv Type is `phone_log`, `greeting_only`, or `noise`**:
   - Still log it (for completeness)
   - Issue Summary = "[PHONE LOG] Inbound call, no text detail" or "[GREETING] No issue described" or "[NOISE] Auto-generated/no content"
   - Issue Category = "none"
   - Sentiment = blank
   - **Do NOT count toward frequency or pattern alerts**

**Step 4: Retroactive matching**
After processing all new conversations:
- For any newly matched contact, scan the Conversation Log for "unmatched" rows with the same phone, email, or contact name
- If found, backfill those rows with the now-known Mx Name, Store ID, and Tier using `mcp__google-workspace__modify_sheet_values`
- Update the corresponding Contact Frequency row to merge the unmatched history into the matched mx
- Report: "Retroactively matched X previous conversations to [mx name] via [phone/email/name]"

**Step 4b: Cross-reference Slack ↔ Intercom**
After processing all new conversations from both sources:
- For each Slack escalation, check if the same mx (by Mx Name or Store ID) has Intercom inbounds in the same 7-day window
- If found, set `Escalated = yes` on the matching Intercom row(s) using `mcp__google-workspace__modify_sheet_values`
- Note the linkage in the Slack row's Thread Context: "Also has X Intercom inbounds this week"
- This linkage feeds into the `escalated_repeat` pattern (Step 5)

**Step 5: Detect patterns**
Analyze the full Conversation Log (existing + newly added). **Only count conversations where Conv Type = `support_issue`, `inquiry`, or `slack_escalation`** — exclude phone_log, greeting_only, and noise from all pattern calculations.

1. **Repeat contact** — same contact (by email, phone, OR name), 3+ valid inbounds in 7 days or 5+ in 30 days
2. **Cross-mx issue** — same issue category from 3+ different mx in 7 days (valid inbounds only)
3. **Sentiment risk** — sentiment score 4+ on an ICP/T1 mx
4. **Resolution gap** — conversation open > 48 hours with no admin response
5. **Gone quiet** — mx had open issues last week, no new activity (may have given up)
6. **Unmatched repeat** — unmatched contact with 2+ valid inbounds — flag for manual identification
7. **Escalated repeat** — mx has both Slack escalation(s) AND Intercom inbound(s) in the same 7-day window. Severity = HIGH. The issue was serious enough to escalate internally AND the mx is reaching out directly.

Check each detected pattern against existing Pattern Alerts to avoid duplicate alerts.

**Step 6: Write to tracker**
- Append new conversation rows to "Conversation Log" tab
- Append new pattern alerts to "Pattern Alerts" tab
- Update "Contact Frequency" tab — recalculate counts for affected contacts

**Step 7: Present findings**

```
## Support Intelligence — [date]

### Active Alerts (X)
- **REPEAT CONTACT** [HIGH] — **Pizza Palace** (Store 12345, ICP) inbounded 5 times in 12 days. Issues: POS sync (3x), payment (2x). Trending up.
- **CROSS-MX ISSUE** [MEDIUM] — "Credit card sync failure" reported by 3 mx this week (Pizza Palace, Burger Barn, Taco Town). Possible platform bug?
- **RESOLUTION GAP** [MEDIUM] — **Sushi Express** open ticket since 3/12 (4 days). No response logged.
- **ESCALATED REPEAT** [HIGH] — **Pizza Palace** (Store 12345, ICP) has 3 Intercom inbounds + 1 Slack escalation this week. Issue: POS sync failure.
- **UNMATCHED REPEAT** [LOW] — Phone 555-1234 has inbounded 3 times, unidentified. Recommend manual lookup.

### Risk Contacts (top 5 by frequency)
| Mx | Store ID | Tier | 7d | 30d | Last Contact | Top Issue |
|----|----------|------|----|-----|-------------|-----------|
| Pizza Palace | 12345 | ICP | 3 | 8 | 2 hours ago | POS sync |

### Retroactive Matches (if any)
- Matched 3 previous "unmatched" conversations to **Pizza Palace** via phone 555-1234

### Triage Summary
- **X valid Intercom inbounds** (support issues + inquiries) — logged and counted
- **Y Slack escalations** — logged and counted
- **Z noise** (phone logs, greetings, auto-generated) — logged but excluded from patterns
- Logged all to tracker. Patterns include both Intercom and Slack.

### New Conversations Logged (Z)
- X valid inbounds (Y matched to mx, W unmatched)
- Updated frequency data for V contacts (valid inbounds only)

### Recommended Actions
- [ ] Investigate POS sync pattern — affects 3 mx, likely product bug
- [ ] Respond to Sushi Express (open 4 days)
- [ ] Proactive check-in with Pizza Palace (high frequency)
- [ ] Manually identify unmatched phone 555-1234 (3 inbounds)
```

---

### Deep Dive Mode

Triggered by: `/support-intel deep dive` or `/support-intel 30 days`

Same as Scan mode but with expanded window (default 30 days) for both Intercom and Slack. Additional:
- Pull conversations in batches (paginate through results)
- Build comprehensive baseline if tracker is new/sparse
- Generate a formatted Google Doc summary report:
  - Use `mcp__google-workspace__import_to_google_doc` with `source_format: "html"`
  - `folder_id`: use the "support intelligence" folder ID from CLAUDE.md Key Folders (subfolder of 2026)
  - Title: "Support Intelligence Report — [date range]"
  - Include all alerts, frequency tables, issue distribution, and trend analysis

---

### Status Mode

Triggered by: `/support-intel status`

Read-only — no new Intercom/Slack pulls, no writes.

1. Read "Pattern Alerts" tab — show all alerts with Status = "new"
2. Read "Contact Frequency" tab — show top 10 contacts by 30d frequency
3. Summarize: total conversations logged, date range covered, alert counts by type

```
## Support Intelligence Status

### Tracker Stats
- **Total conversations logged:** N
- **Date range covered:** [earliest] to [latest]
- **Contacts tracked:** X (Y matched, Z unmatched)

### Active Alerts (X)
[list alerts with Status = "new"]

### Top Contacts by Frequency (30 days)
[table of top 10]

### Issue Distribution
- POS/technical: X conversations (Y%)
- Payment: X (Y%)
- ...
```

---

## Example usage

```
/support-intel                  ← daily scan (last 48h)
/support-intel deep dive        ← 30-day comprehensive analysis
/support-intel 7 days           ← scan with custom window
/support-intel status           ← read-only current state
```
