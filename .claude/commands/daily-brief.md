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

### 2. Card Metrics (executive-level)
- Run the daily-only portion of the card metrics query via `mcp__ask-data-ai__ExecuteSnowflakeQuery`:

```sql
with
  kiosk_only as (
    select store_id, store_name,
      min(submit_platform) as min_submit_platform,
      max(submit_platform) as max_submit_platform
    from edw.pathfinder.fact_pathfinder_orders
    where active_date >= '2023-01-01' and store_id not in (30553809)
    group by 1, 2
    having min_submit_platform = 'self_kiosk' and max_submit_platform = 'self_kiosk'
  ),
  base_daily as (
    select psd.calendar_date, psd.store_id,
      psd.total_card_orders as card_volume,
      psd.total_card_gov as card_gov
    from edw.pathfinder.agg_pathfinder_stores_daily psd
    where psd.calendar_date >= dateadd(day, -14, current_date)
      and psd.store_id not in (select store_id from kiosk_only)
  ),
  per_store_daily as (
    select date_trunc('day', calendar_date) as period_date,
      store_id,
      sum(card_volume) as store_card_volume,
      sum(card_gov) as store_card_gov
    from base_daily
    group by 1, 2
  ),
  agg as (
    select period_date,
      count(distinct iff(store_card_volume >= 70, store_id, null)) as n_active_stores,
      sum(store_card_volume) as card_volume,
      sum(store_card_gov) as card_gov
    from per_store_daily
    group by 1
  )
select period_date, n_active_stores, card_volume, card_gov,
  lag(n_active_stores) over (order by period_date) as prev_active_stores,
  lag(card_volume) over (order by period_date) as prev_card_volume,
  lag(card_gov) over (order by period_date) as prev_card_gov,
  (n_active_stores - prev_active_stores) / nullif(prev_active_stores, 0) as pct_chg_active_stores,
  (card_volume - prev_card_volume) / nullif(prev_card_volume, 0) as pct_chg_card_volume,
  (card_gov - prev_card_gov) / nullif(prev_card_gov, 0) as pct_chg_card_gov,
  lag(n_active_stores, 7) over (order by period_date) as prev_active_stores_7d,
  lag(card_volume, 7) over (order by period_date) as prev_card_volume_7d,
  lag(card_gov, 7) over (order by period_date) as prev_card_gov_7d,
  (n_active_stores - prev_active_stores_7d) / nullif(prev_active_stores_7d, 0) as pct_chg_active_stores_7d,
  (card_volume - prev_card_volume_7d) / nullif(prev_card_volume_7d, 0) as pct_chg_card_volume_7d,
  (card_gov - prev_card_gov_7d) / nullif(prev_card_gov_7d, 0) as pct_chg_card_gov_7d
from agg
order by period_date desc
limit 1
```

- **Data freshness check:** The latest `period_date` should be yesterday (today - 1). If it's older, display "Card metrics data not yet available for yesterday. Latest: [actual date]." instead of the table. Do NOT present stale data as current.
- Present the latest daily row as a table (see Compile section below)
- Flag any metric with >10% day-over-day swing or >15% vs 7 days ago

### 3. Calendar
- Use `mcp__google-workspace__get_events`:
  - `user_google_email: "philip.bornhurst@doordash.com"`
  - `time_min`: today start, `time_max`: today end
- List meetings chronologically with time, title, duration, attendees
- Flag first meeting and any mx calls needing prep

### 4. Email
- Use `mcp__google-workspace__search_gmail_messages`:
  - `user_google_email: "philip.bornhurst@doordash.com"`
  - `query: "is:unread"`
- Summarize top 5-10 most important unread messages
- Flag anything urgent or time-sensitive

### 5. Slack Escalations + Intercom Inbounds (PARALLEL)
Fire both Slack and Intercom calls **in the same tool call batch** so neither blocks the other.

**Slack (required):**
- Use `mcp__slack__slack_read_channel` on #pathfinder-support (C067SSZ1AMT)
- Scan last 24 hours for escalations mentioning Phil's mx
- **CRITICAL:** The `oldest` and `latest` parameters MUST be **Unix epoch timestamps** (integer seconds since Jan 1, 1970), NOT date strings. Compute the timestamp first (e.g., for 24h ago: `int((datetime.now() - timedelta(days=1)).timestamp())`).
- Flag anything needing response

**Intercom (parallel, skip on failure):**
- Use `mcp__intercom__search_conversations` for last 24 hours
- **RESILIENCE RULE:** If `search_conversations` fails, errors, or returns an error response, **skip the entire Intercom section immediately** — do NOT retry. Display: "Intercom unavailable — connection failed. Run `/intercom` separately when it's back up."
- If the search succeeds, read up to **5 conversations max** via `mcp__intercom__get_conversation` — do not go deeper
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

## Card Metrics (daily)
| Metric | Today ([date]) | Prior Day | Δ | 7 Days Ago | Δ |
|--------|----------------|-----------|---|------------|---|
| Active Stores (≥70) | X | Y | +Z.Z% | A | +B.B% |
| Card Volume | X | Y | +Z.Z% | A | +B.B% |
| Card GOV | $X | $Y | +Z.Z% | $A | +B.B% |
[Flag notable movements: >10% DoD or >15% vs 7d ago]

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
