# /intercom — Intercom Support Inbox

Check Intercom for recent mx inbound support texts, or search a specific mx's support history.

> Intercom is the **primary inbound support channel** — all mx support texts come through here. Slack #pathfinder-support only contains escalated issues (a small subset).

## Instructions

**Determine mode from input:**
- No args or time window (e.g., "last 3 days") → **Recent inbounds mode**
- mx name, Store ID, or contact info provided → **mx-specific mode**

---

### Recent Inbounds Mode (default)

1. **Fetch recent conversations** — Use `mcp__intercom__search_conversations`:
   - Default: last 24 hours. User can specify a different window.
   - Surface all conversations, prioritizing open/unresolved ones.

2. **Read full thread and triage each conversation:**
   For each conversation, use `mcp__intercom__get_conversation` to pull ALL conversation parts (not just metadata or latest message).

   a. **Classify Conv Type** based on the full thread:
      - `support_issue` — mx describes an actual problem (includes conversations ending with "It worked. Thank you." — the issue is real, just resolved)
      - `inquiry` — mx asking a question (how do I do X, what's the status of Z)
      - `phone_log` — auto-logged inbound call with no/minimal text
      - `greeting_only` — only greetings, no substantive follow-up
      - `noise` — spam, test messages, auto-generated entries

   b. **Extract the ORIGINAL issue** — Scan the full thread chronologically. Find the mx's FIRST substantive message(s) describing the problem or question. The Issue Summary must describe the ORIGINAL problem, not the latest reply.

   c. **Identify the mx** (for valid inbounds):
      - Check the contact's company/business name field in the conversation
      - If unclear, use `mcp__intercom__get_contact` to pull full contact details (name, email, phone, custom attributes)
      - Cross-reference against Master Hub (`mcp__google-workspace__read_sheet_values`):
        - `spreadsheet_id: "1ndVs2lPhS5frpkEV0KzK7ec5aS18fmr9h1BQEu099E4"`
        - `user_google_email: "philip.bornhurst@doordash.com"`
        - Search by business name, contact name, phone number, or email
      - If matched, include Store ID, tier, and portal link in output

3. **Enrich with pattern context** (if Support Intelligence Tracker exists):
   - Check CLAUDE.md Key Spreadsheets for "Support Intelligence Tracker"
   - If found, read "Contact Frequency" tab and "Conversation Log" tab
   - For each conversation contact, check if they have a high frequency count or Risk Flag = "yes"
   - Annotate those contacts in the output: `[REPEAT: 5 inbounds in 12 days]`
   - Also check if the mx has any Slack escalations logged in the SIT (Source = `slack`). If so, annotate: `[ESCALATED: Slack escalation on 3/12]`
   - If SIT doesn't exist, skip this step (no error)

4. **Present** — Only show `support_issue` and `inquiry` conversations in the main list. Show noise as a collapsed count.

```
## Intercom Inbounds — Last 24 Hours
**Valid inbounds:** N | **Open:** X | **Closed:** Y
(Excluded: Z phone logs/greetings/noise — logged but not shown)

### Open / Needs Response (X)
- **[mx name]** (Store ID: XXXXX, Tier: ICP) — Issue summary (conv ID, opened X hours ago) [REPEAT: 5 inbounds in 12 days] [ESCALATED: Slack escalation on 3/12]
  Portal: https://www.doordash.com/merchant/sales?store_id=XXXXX
- **[Contact name]** (unmatched) — Issue summary (conv ID, opened X hours ago)

### Recently Closed (Y)
- **[mx name]** — Issue summary (closed X hours ago)
- ...

### Summary
- X open conversations needing response
- Y closed in last 24h
- Z noise excluded (phone logs, greetings, auto-generated)
- Notable: [any ICP/T1 mx, repeat contacts, urgent themes]
- Pattern flags: [any contacts flagged by Support Intelligence Tracker]
```

---

### mx-Specific Mode

1. **Search for the mx** — Use `mcp__intercom__search_conversations` with the mx name or contact info.
   - Also try `mcp__intercom__search_contacts` to find the contact by name, email, or phone.
   - If a Store ID is provided, first look up the mx name from Master Hub, then search Intercom.

2. **Get full details** — Use `mcp__intercom__get_conversation` on the most recent 5 conversations. Read the FULL thread for each — extract the ORIGINAL issue from the mx's first substantive messages, not the latest reply.

3. **Classify each conversation** — Label Conv Type: `[SUPPORT]`, `[INQUIRY]`, `[PHONE]`, `[GREETING]`, `[NOISE]`. This gives full history context while making it clear what's substantive.

4. **Present:**

```
## Intercom History: [Merchant Name]
**Store ID:** XXXXX | **Tier:** ICP | **Total conversations:** N (X valid inbounds, Y noise)
**Portal:** https://www.doordash.com/merchant/sales?store_id=XXXXX

### Conversation Timeline
- [date] [SUPPORT] — Issue summary from original problem (status: open/closed)
  Key details from conversation parts
- [date] [INQUIRY] — Question summary (status: closed)
  Key details
- [date] [PHONE] — Inbound call, no text detail (status: closed)
- ...

### Patterns
- Most common issues: [themes from valid inbounds only]
- Valid inbound frequency: X in last 30 days
- Last contact: [date]
- **Support Intelligence:** [If SIT exists, show frequency data from Contact Frequency tab — 7d/30d/90d counts, risk flag status, top issues over time]
```

## Example usage

```
/intercom                    ← recent inbounds (last 24h)
/intercom last 3 days        ← adjust time window
/intercom Pizza Palace       ← support history for specific mx
/intercom Store 12345        ← lookup by Store ID
/intercom open only          ← only show open/unresolved
```
