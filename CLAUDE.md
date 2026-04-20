# Launchpad — Phil's Homebase

> Command center for Pathfinder Account Management. All MCP tools, all workflows, one workspace.

---

## About Me

- **Name:** Philip Bornhurst (Phil)
- **Role:** Head of Account Management for Pathfinder, Strategy and Operations team at DoorDash Commerce Platform
- **Email:** [philip.bornhurst@doordash.com](mailto:philip.bornhurst@doordash.com)
- **Timezone:** America/Los_Angeles (PST/PDT)
- **Team:** One direct report — Mallory Thornley (Account Manager)

---

## What I Work On

- **Account Management:** Managing mx relationships for Pathfinder (DoorDash's POS product)
- **Account Health:** Monitor volume trends, account status, merchant satisfaction (MSAT scores)
- **Merchant Calls:** Intro calls, check-ins, QBRs with restaurant partners
- **Product Feedback:** Collect and track mx feature requests and pain points
- **Support Escalations:** Track escalated issues from #pathfinder-support and Intercom
- **Sales/Launch Handoffs:** After Sales hands off to Launch, Launch hands off to AM post go-live.
- **Strategic Initiatives:** Drive adoption of ancillary products (Gift Cards, Kiosk, OCL, Mobile App, 1p Online Ordering)

---

## Terminology


| Term | Meaning                                                        |
| ---- | -------------------------------------------------------------- |
| mx   | Merchant (always lowercase)                                    |
| POS  | Point of Sale                                                  |
| GOV  | Gross Order Value                                              |
| QBR  | Quarterly Business Review                                      |
| MSAT | Merchant Satisfaction Score                                    |
| ICP  | Ideal Customer Profile (highest priority tier)                 |
| OCL  | Omni-Channel Loyalty                                           |
| 1p   | First-party (online ordering)                                  |
| OSW  | Order Success Widget                                           |
| AM   | Account Manager                                                |
| DRI  | Directly Responsible Individual                                |
| xfn  | Cross-functional                                               |
| SIT  | Support Intelligence Tracker (pattern detection spreadsheet)   |
| Puck | M2 Stripe card reader (newer hardware, replacing Wise readers) |
| Wise | WisePOS card reader (legacy hardware, being phased out)        |
| M2   | Stripe M2 reader, also called "puck"                           |
| CFD  | Customer-Facing Display                                        |


---

## Communication Style

- **Slack:** Direct, concise, action-oriented. Use mx names and Store IDs for clarity.
- **Emails:** Professional but warm with mx. Data-driven with internal teams.
- **Call Notes:** Bullet-heavy summaries with action items, MSAT scores, and follow-up dates.
- **Avoid:** Over-explanation, consultant speak, asking permission for routine tasks. Default to action.

---

## MCP Servers & Tools

### google-workspace (unified, project-local)

- **Server:** `uvx workspace-mcp` (stdio)
- **Covers:** Gmail, Calendar, Sheets, Drive, Docs
- **CRITICAL:** Every tool call requires `user_google_email: "philip.bornhurst@doordash.com"`

Key tools by domain:

- **Gmail:** `search_gmail_messages`, `get_gmail_message_content`, `get_gmail_thread_content`, `draft_gmail_message`, `send_gmail_message`
- **Calendar:** `get_events`, `manage_event`, `list_calendars`, `query_freebusy`
- **Drive:** `search_drive_files`, `get_drive_file_content`, `list_drive_items`
- **Sheets:** `read_sheet_values`, `modify_sheet_values`, `get_spreadsheet_info`, `list_spreadsheets`
- **Docs:** `get_doc_content`, `get_doc_as_markdown`, `create_doc`, `search_docs`

### slack (HTTP/OAuth, global)

- **Tools:** `slack_list_channels`, `slack_search_public_and_private`, `slack_search_users`, `slack_read_channel`, `slack_post_message`
- **CRITICAL — `oldest`/`latest` parameters:** The `slack_read_channel` tool's `oldest` and `latest` parameters require **Unix epoch timestamps** (integer seconds since Jan 1, 1970), NOT date strings. Passing a date string like `"2026-02-14"` will silently fail and return messages from the beginning of the channel. Always compute the Unix timestamp first (e.g., 2026-02-14 00:00:00 PST → `1739520000`). Use Python or shell `date` to compute if needed.
- **Key channels:**
  - #pathfinder-support (C067SSZ1AMT) — escalations
  - #pathfinder-mxonboarding (C067E67HNAZ) — onboarding coordination
  - #phils-gumloop-agent (C0AC2NK50QN) — test/posting channel

### ask-data-ai (HTTP, global)

- **Tools:** `ExecuteSnowflakeQuery`, `search_data_catalog`, `ask_data_mx`, `DescribeTable`, `ask_analytics_ai`, `ask_firefly`, `discover_sigma_dashboards`, `ask_finance_ai`, `ask_ai_network`

### nanobanana (Gemini image generation, project-local)

- **Server:** `uvx nanobanana-mcp-server@latest` (stdio)
- **Capabilities:** AI image generation with multiple Gemini models, smart templates, aspect ratio control, up to 4K resolution
- **Key tools:** `generate_image`, `edit_image`, `list_models`, `list_templates`
- **Usage:** "Generate an image of..." — best for high-quality image generation

### gemini (Full Gemini suite, project-local)

- **Server:** `npx -y @rlabs-inc/gemini-mcp` (stdio)
- **Capabilities:** Deep research, document analysis, YouTube analysis, Google Search, text generation, code execution, image generation, video generation (Veo)
- **Key tools:** `generate_image`, `deep_research`, `search`, `analyze_document`, `analyze_youtube`, `generate_text`, `generate_video`
- **Usage:** "Research...", "Analyze this YouTube video...", "Generate a video of..."

### intercom (official, remote via .mcp.json)

- **Server:** `npx mcp-remote https://mcp.intercom.com/mcp` (stdio bridge to Cloudflare)
- **Auth:** OAuth (browser popup on first connection, then cached)
- **Capabilities:** Search/retrieve Intercom conversations and contacts
- **Key tools:** `search`, `fetch`, `search_conversations`, `get_conversation`, `search_contacts`, `get_contact`
- **Usage:** "Check Intercom for recent tickets from [mx]", "Pull the Intercom conversation for [issue]"

### pocket (remote via .mcp.json)

- **Server:** `npx mcp-remote https://public.heypocketai.com/mcp` (stdio bridge)
- **Auth:** OAuth (browser popup on first connection, then cached)
- **Usage:** "Ask Pocket...", "Use Pocket to..."

---

## Support Channels


| Channel                                | Type                    | What goes here                                                                  |
| -------------------------------------- | ----------------------- | ------------------------------------------------------------------------------- |
| Intercom                               | Primary inbound         | ALL mx support texts. Every mx inquiry comes through here. High volume.         |
| #pathfinder-support (C067SSZ1AMT)      | Escalation layer        | Critical, novel, or internally-escalated issues only. Small subset of Intercom. |
| #pathfinder-mxonboarding (C067E67HNAZ) | Onboarding coordination | New mx onboarding, hardware installs, launcher visits.                          |


- "Support texts" / "inbounds" / "tickets" → check **Intercom**
- "Escalations" → check **Slack #pathfinder-support**
- "Onboarding" / "installs" / "launches" → check **Slack #pathfinder-mxonboarding**
- For a full picture, check both support channels (Intercom + #pathfinder-support)
- **mx identification:** Intercom contacts may not always show business name. Cross-reference against Master Hub by business name, phone, or contact email when needed.

---

## Card Readers (Hardware)

Pathfinder uses Stripe-powered card readers for in-store credit card payments. There are two types in the field:


| Reader               | Also Called       | Status                           | Notes                                                                                              |
| -------------------- | ----------------- | -------------------------------- | -------------------------------------------------------------------------------------------------- |
| **M2 Stripe Reader** | Puck, M2 Puck     | **Current** — actively deploying | Newer hardware, replacing Wise. Connects via USB to the Elo POS.                                   |
| **WisePOS Reader**   | Wise, Wise reader | **Legacy** — being phased out    | Older hardware. Some setups are not compatible with M2, so Wise remains in use at those locations. |


- "Puck" and "M2 reader" are interchangeable — both refer to the Stripe M2 reader.
- The rollout strategy is to replace all Wise readers with Pucks over time.
- Card reader issues are among the most common support inbounds (disconnection, chip failures, hardware defects).
- For card reader troubleshooting, common steps include: reboot POS, unplug/replug USB, check USB port color (blue vs orange on A14 devices), unlock ports in EloView, unplug power strip entirely.

---

## Key Spreadsheets


| Name                         | Spreadsheet ID                                 | Primary Sheet        |
| ---------------------------- | ---------------------------------------------- | -------------------- |
| Master Hub                   | `1ndVs2lPhS5frpkEV0KzK7ec5aS18fmr9h1BQEu099E4` | (default)            |
| Product Feedback Tracker     | `1-EylRCLxhpStfEoj-8ga9Ex_26dHBoWgxU6Yr_hT0Y4` | The Final Final Boss |
| Volume Drop Data             | `1bu0fWwKWQQeI8nrkhGKA68dTzKRtIh_MXAPeqze0NX0` | (default)            |
| Support Intelligence Tracker | `1XduutDkGbvZpe9kGyoW9d1_zW08iHxFnVzxxltP7w5U` | Conversation Log     |


---

## Key Data Tables (Snowflake)


| Table                                                            | What                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| ---------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `edw.pathfinder.agg_pathfinder_stores_daily`                     | Daily per-store card volume and GOV — the core Pathfinder business metrics                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `edw.pathfinder.fact_pathfinder_orders`                          | Order-level detail (used to identify kiosk-only stores for exclusion)                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| `proddb.public.pathfinder_merchant_database_from_gsheet_cleaned` | Mx lifecycle dates: close/win (CW) date, onboarding call date                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `edw.merchant.dimension_store`                                   | Store name, cuisine type                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| `edw.merchant.dimension_business`                                | Business-level attributes: management type (grouped and detailed)                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| `edw.merchant.fact_merchant_orders_portal`                       | Order-level data with channel, operations (avoidable wait, cancellations, errors), customer type (new/repeat), ratings — primary table for QBRs                                                                                                                                                                                                                                                                                                                                                                   |
| `edw.merchant.fact_merchant_order_items`                         | Item-level product mix: item name, category, subtotal, quantity, missing/incorrect flags                                                                                                                                                                                                                                                                                                                                                                                                                          |
| `edw.merchant.fact_menu_performance_daily`                       | Menu conversion funnel: visits, checkouts, deliveries, photo coverage by store/day                                                                                                                                                                                                                                                                                                                                                                                                                                |
| `edw.merchant.fact_merchant_transactions_details_portal`         | Financial transaction details: subtotal, fees, commissions, discount breakdowns by channel — source of merchant Financial Report CSV. **Key columns:** `channel` (Marketplace, In-store, Kiosk, Storefront), `subtotal`, `tax_amount`, `discount_paid_by_doordash/mx/third_party_contribution`. **Critical:** In-store/Kiosk orders have `final_order_status = 'Picked Up'`, not `'Delivered'`. Always filter `final_order_status IN ('Delivered', 'Picked Up')` to include all completed orders across channels. |
| `edw.ads.fact_promo_campaign_performance`                        | Promo marketing campaigns: orders, sales, mx/DD/3rd-party funded discounts, marketing fees, ROAS, CX acquisition. Amounts in cents. Filter: `report_type='campaign_store' AND timezone_type='utc' AND daypart_name='day'`                                                                                                                                                                                                                                                                                         |
| `edw.ads.fact_sl_campaign_performance`                           | Sponsored listing campaigns: impressions, clicks, orders, sales, ad fees, ROAS, CX acquisition. Amounts in cents. Same filter as promo table.                                                                                                                                                                                                                                                                                                                                                                     |
| `proddb.public.ddoo_mp_geo_cuisine_performance`                  | Monthly per-store marketplace performance by city/cuisine: orders, GOV, AOV, customers, ratings, promo spend. Used by location-scout agent for competitive benchmarking.                                                                                                                                                                                                                                                                                                                                          |
| `edw.merchant.fact_merchant_sales`                               | Near-realtime order-level data (~minutes latency). Used by mx-alert-monitor for intraday volume checks. **Key columns:** `store_id`, `channel` (In-store, Kiosk, Marketplace, Storefront), `transaction_created_at_local`, `subtotal`. POS channels = `channel IN ('In-store', 'Kiosk')`.                                                                                                                                                                                                                         |


These are the **executive-level** Pathfinder POS business tables. Use them for total business reporting: active stores, card volume, card GOV, period-over-period trends.

### Snowflake query routing

- **Default: ask-data-ai** for everything that isn't a raw SQL scan — `ask_firefly`, `search_data_catalog`, `DescribeTable`, `discover_sigma_dashboards`, `ask_data_mx`, `ask_finance_ai`, and the other wiki/metric agents. These are fast and don't hit OAuth drops.
- **Fall back to direct Snowflake** for raw SQL via `python3 scripts/snowflake_query.py --json "SQL_HERE"`. Auth is PAT from `.env`. No browser, no keychain, no OAuth.
- **Always use direct Snowflake for:** audit tables (`fact_menu_audit_event_changes_daily`, `iguazu.server_events_production.menu_audit_event`), wide scans (>30 days), or any query you expect to run >30s. `mcp__ask-data-ai__ExecuteSnowflakeQuery` drops connection every ~2min and returns `"Downstream not connected"`.

### POS Cohort Query (per-mx)

The canonical query for **per-mx lifecycle and performance data** — returns the entire POS cohort (live and churned) with lifecycle dates, segments, and key weekly metrics. Use this when researching a specific mx or reporting on individual mx performance.

**Key per-mx metrics:**

- **Lifetime OSW** (Orders per Store Week): `7 * (lifetime_card_orders / total_active_days)` — avg weekly in-store CC transactions
- **Lifetime GOV Store Week**: `7 * (lifetime_card_gov / total_active_days)` — avg weekly in-store GOV
- **AOV**: `lifetime_card_gov / lifetime_card_orders`
- **Go-active date**: first date where trailing 7d card orders ≥ 70
- **Sustained activation**: ≥70 orders/week maintained 7+ days after go-active

**Full SQL** (filter by `WHERE pf.store_id = [STORE_ID]` for a single mx):

```sql
with
  kiosk_only as (
    select store_id,
      min(submit_platform) as min_submit_platform,
      max(submit_platform) as max_submit_platform
    from edw.pathfinder.fact_pathfinder_orders
    where active_date >= '2023-01-01' and store_id not in (30553809)
    group by all
    having min_submit_platform = 'self_kiosk' and max_submit_platform = 'self_kiosk'
  ),
  store_dates as (
    select store_id, cw_date, OB_CALL_DATE_CLEANED as ob_date
    from proddb.public.pathfinder_merchant_database_from_gsheet_cleaned
    qualify row_number() over (partition by store_id order by cw_date desc) = 1
  ),
  pf as (
    select
      psd.store_id,
      psd.live_date as install_date,
      sd.cw_date,
      sd.ob_date,
      datediff('days', try_to_date(sd.cw_date), try_to_date(sd.ob_date)) as cs_to_ob_days,
      datediff('days', try_to_date(sd.ob_date), try_to_date(psd.live_date)) as ob_to_install_days,
      min(iff(psd.total_card_orders_l7d >= 70, psd.calendar_date, null)) as go_active_date,
      max(iff(psd.total_card_orders > 0, psd.calendar_date, null)) as last_card_order_date,
      datediff('day', go_active_date, last_card_order_date) + 1 as total_active_days,
      sum(psd.total_card_orders) as lifetime_card_orders,
      sum(psd.total_card_gov) as lifetime_card_gov,
      lifetime_card_gov / nullif(lifetime_card_orders, 0) as aov,
      7 * (sum(psd.total_card_orders) / nullif(total_active_days, 0)) as lifetime_osw,
      7 * (sum(psd.total_card_gov) / nullif(total_active_days, 0)) as lifetime_gov_store_week
    from edw.pathfinder.agg_pathfinder_stores_daily psd
      left join store_dates sd on psd.store_id::varchar = sd.store_id::varchar
    where psd.store_id not in (select distinct store_id from kiosk_only)
    group by all
  ),
  sustained as (
    select d.store_id,
      d.calendar_date as first_sustained_date,
      d.total_card_orders_l7d
    from edw.pathfinder.agg_pathfinder_stores_daily d
      join pf on d.store_id = pf.store_id
    where d.calendar_date >= dateadd(day, 7, pf.go_active_date)
      and d.total_card_orders_l7d >= 70
    qualify row_number() over (partition by d.store_id order by d.calendar_date) = 1
  )
select
  ds.name as store_name,
  ds.cuisine_type,
  pf.*,
  db.management_type_grouped,
  db.management_type,
  s.total_card_orders_l7d as osw_after_go_active,
  s.first_sustained_date::date as date_sustained_activation,
  iff(s.first_sustained_date is not null, 'yes', 'no') as met_activation_threshold,
  case
    when s.first_sustained_date is null then null
    when datediff('days', pf.go_active_date, s.first_sustained_date) = 7 then 'yes'
    else 'no'
  end as met_activation_threshold_first_7d
from pf
  join edw.merchant.dimension_store ds on pf.store_id = ds.store_id
  join edw.merchant.dimension_business db on ds.business_id = db.business_id
  left join sustained s on pf.store_id = s.store_id
order by 1
```

---

## Merchant Tiers (Priority Order)

1. **ICP** — Ideal Customer Profile (highest priority)
2. **Tier 1** — High-impact mx
3. **Tier 2** — Mid-tier accounts
4. **Tier 3** — Standard accounts

Focus extra attention on ICP and Tier 1 for proactive outreach and issue resolution.

---

## Key Links

- **Master Hub:** [https://docs.google.com/spreadsheets/d/1ndVs2lPhS5frpkEV0KzK7ec5aS18fmr9h1BQEu099E4/edit](https://docs.google.com/spreadsheets/d/1ndVs2lPhS5frpkEV0KzK7ec5aS18fmr9h1BQEu099E4/edit)
- **Product Feedback Tracker:** [https://docs.google.com/spreadsheets/d/1-EylRCLxhpStfEoj-8ga9Ex_26dHBoWgxU6Yr_hT0Y4/edit](https://docs.google.com/spreadsheets/d/1-EylRCLxhpStfEoj-8ga9Ex_26dHBoWgxU6Yr_hT0Y4/edit)
- **Volume Drop Data:** [https://docs.google.com/spreadsheets/d/1bu0fWwKWQQeI8nrkhGKA68dTzKRtIh_MXAPeqze0NX0/edit](https://docs.google.com/spreadsheets/d/1bu0fWwKWQQeI8nrkhGKA68dTzKRtIh_MXAPeqze0NX0/edit)
- **Merchant Portal:** `https://www.doordash.com/merchant/sales?store_id=[STORE_ID]`

---

## Rules

1. **Default to action** — When I say "check emails," fetch them immediately. Don't ask if I want you to.
2. **Cross-reference everything** — For mx questions, pull Master Hub data, running notes, support tickets, volume data, and web search for location context.
3. **Exact filtering** — When filtering spreadsheets by Account Manager or any column, use EXACT matches. Don't guess or approximate.
4. **Volume alerts** — Prioritize mx who went dark (previous volume > 0, current = 0 or null).
5. **Always include Store ID** — When referencing a mx, include their Store ID and merchant portal link.
6. **Use "mx"** — Always refer to merchants as "mx" (lowercase).
7. **Show your work** — When filtering data, explicitly state: "Filtering for: Account Manager = 'Phil Bornhurst' AND Status = 'Live'"
8. **google-workspace email** — ALWAYS pass `user_google_email: "philip.bornhurst@doordash.com"` to every google-workspace tool call. No exceptions.
9. **Gmail rate limits** — Complete all Calendar calls BEFORE fetching emails. Only ONE gmail read call per function batch.
10. **Confirm before sending** — Never send Slack messages, emails, or modify spreadsheet data without explicit user approval. Draft and show first.
11. **Call prep** — For mx calls, pull running notes, recent MSAT, support tickets, and volume trends before the call.
12. **Timezone** — All times in America/Los_Angeles unless specified otherwise.

---

## Daily Briefing

- **Command:** `/daily-brief` or "Compile my morning brief"
- **Architecture:** 4 parallel sub-agents (Volume+Metrics, Calendar+Email, Slack+Intercom, Pattern Alerts) orchestrated by the `briefing-compiler` agent
- **Delivery:** Styled HTML email to Phil + condensed Slack summary to #phils-gumloop-agent (C0AC2NK50QN)
- **Automation:** macOS launchd runs `scripts/daily-briefing.sh` at 8am daily (fires on wake if Mac was asleep). Future: Claude Agent SDK server-side deployment.
- **Sections:** Volume Alerts → Card Metrics → Today's Calendar → Email Summary → Slack Escalations → Intercom Inbounds → Pattern Alerts → Action Items
- **Error handling:** Each sub-agent runs independently. If any data source fails, that section shows "unavailable" — the rest of the briefing still delivers. No retries.

---

## Proactive Monitoring

- **Persistent:** macOS launchd runs `scripts/mx-alert-monitor.sh` 3x daily (10:30am, 2:30pm, 5:30pm PST). Uses intraday Snowflake data (`fact_merchant_sales`) to compare today-so-far vs same time window last week. Channel-specific alerting: POS dark + Marketplace active = HIGH alarm (possible churn).
- **Ad-hoc:** Say "Watch my portfolio" to create a CronCreate job (session-only, 3-day expiry) for more frequent checks.
- **On-demand:** `/mx-alert-monitor` runs a single check immediately.
- **Full analysis:** `/churn-risk` runs the full health score agent with Google Doc output.

---

## Skills


| Command             | Purpose                                                                                                                       |
| ------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `/daily-brief`      | Morning briefing: volume alerts + calendar + email + support                                                                  |
| `/gcal-today`       | Show today's calendar and upcoming meetings                                                                                   |
| `/gmail-search`     | Search Gmail inbox                                                                                                            |
| `/gdrive-search`    | Search Google Drive for files                                                                                                 |
| `/slack-search`     | Search Slack messages and channels                                                                                            |
| `/slack-send`       | Compose and send a Slack message                                                                                              |
| `/data-query`       | Query DoorDash data warehouse via ask-data-ai                                                                                 |
| `/mx-lookup`        | Cross-reference a mx across all data sources                                                                                  |
| `/call-prep`        | Prepare for a mx call with full context                                                                                       |
| `/intercom`         | Check Intercom inbounds (all mx support texts) or search mx support history                                                   |
| `/support-scan`     | Combined support scan: Slack escalations + Intercom highlights + pattern alerts                                               |
| `/support-intel`    | Support pattern analysis: repeat inbounders, cross-mx issues, risk flags                                                      |
| `/weekly-recap`     | Weekly summary across all tools                                                                                               |
| `/weekly-mindmap`   | Weekly cross-AM mind map (Phil + Mallory): themes, risks, wins, product feedback, stakeholder graph. Google Doc in `Weekly Mind Maps 2026`. |
| `/card-metrics`     | Pathfinder card volume metrics: active stores, volume, GOV with period-over-period changes                                    |
| `/feedback-log`     | Log product feedback to the tracker                                                                                           |
| `/meeting-capture`  | Scan last 7d Granola for `mx call` flagged meetings, generate PRISM-TnA from transcript, prepend to Running Notes doc, log    |
| `/location-scout`   | 360° location analysis: demographics, competition, traffic drivers, DoorDash market data                                      |
| `/calendly-prep`    | Prep for today's Calendly calls: scan calendar, match Master Hub, create folders/docs, internet research, Slack summary       |
| `/churn-risk`       | Portfolio health scores: composite RED/YELLOW/GREEN per mx with churn risk ranking                                            |
| `/mx-alert-monitor` | Intraday anomaly check: POS-dark detection, channel-specific churn signals, volume drops >40%. Uses real-time Snowflake data. |
| `/autoreason`       | Adversarial refinement: critique, rewrite, synthesis, blind judging until convergence                                         |


---

## Agents

Agents run as isolated subprocesses — they pull from multiple data sources in their own context and return a polished result. They can run in the **background** while you keep working.


| Agent                | Trigger                                                                                           | What it does                                                                                                                                                                                                                       |
| -------------------- | ------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `mx-researcher`      | "Research [mx]", "Deep dive on [mx]", "Give me everything on [mx]"                                | Comprehensive mx dossier: Master Hub + Volume + Slack + Email + Feedback + Running Notes + Snowflake. Auto-creates a formatted Google Doc in the `mx deep dives` folder and shares with doordash.com.                              |
| `briefing-compiler`  | "Compile my morning brief", "Run my daily brief in the background"                                | Daily/weekly briefing via 4 parallel sub-agents (Volume+Metrics, Calendar+Email, Slack+Intercom, Pattern Alerts). Outputs styled HTML email + Slack summary. Graceful degradation if any source fails.                             |
| `support-intel`      | "Run a deep support analysis", "Build the support intelligence baseline"                          | Deep pattern analysis across Intercom conversations. Detects repeat inbounders, cross-mx issues, sentiment risks. Produces Google Doc report.                                                                                      |
| `qbr-generator`      | "Generate a QBR for [mx]", "QBR for Store 12345, Jan-Mar 2026"                                    | Full QBR data package via 4 parallel sub-agents: channel performance, operations, product mix, customer data, marketing. Opus-powered strategic insights. Outputs local .md (for NotebookLM) + Google Doc.                         |
| `location-scout`     | "Research [address] for [cuisine]", "Scout [city] for burgers", "Location analysis for [address]" | 360° location research: demographics + competition + traffic drivers + DoorDash marketplace data via 4 parallel sub-agents. Produces merchant-facing Google Doc with GO/CONDITIONAL/NO-GO recommendation.                          |
| `calendly-call-prep` | "Prep my Calendly calls", "Run Calendly prep", `/calendly-prep`                                   | Scans today's calendar for Calendly events, matches to Master Hub, creates account management folder + Running Notes doc, runs Opus-powered internet research, sends Slack notification with links and restaurant brief.           |
| `churn-risk`         | "Run churn risk analysis", "Health score report", "Which mx are at risk"                          | Portfolio health scoring: 3 parallel sub-agents (volume, support, engagement). Composite RED/YELLOW/GREEN per mx. NEW vs. ONGOING risk detection. Opus-powered scoring + recommendations. Google Doc report + daily brief summary. |
| `autoreason`         | "Autoreason this:", "/autoreason [task]", "Refine [task] through adversarial iteration"           | Adversarial multi-agent refinement. Author → Strawman → Rewrite → Synthesize → 3 Blind Judges per round. Loops until incumbent wins twice (streak=2) or max rounds. Opus generators + Sonnet judges.                               |
| `weekly-mindmap`     | "Build a weekly mind map", "Weekly mind map for week of 4/13", `/weekly-mindmap`                  | Weekly cross-AM mind map. Pulls Phil+Mallory calls from input tracker, dispatches N parallel extraction sub-agents (one per AM book), synthesizes themes/risks/wins/feedback/stakeholder graph. Outputs Google Doc in `Weekly Mind Maps 2026`. |


**Usage:** Just describe what you want naturally, or be explicit ("Use the mx-researcher agent"). Add "in the background" to run while you keep working.

---

## Google Docs Formatting

When creating Google Docs (dossiers, reports, briefs, etc.), always use the `import_to_google_doc` tool with `source_format: "html"` to produce beautifully formatted documents. Never use `create_doc` with plain text.

**Style guide:**

- **Headings:** Dark slate `#2C3E50` for H1/H2, `#34495E` for H3. No red in titles.
- **Table headers:** `background-color: #2C3E50; color: white;`
- **Alternating rows:** `tr:nth-child(even) { background-color: #f9f9f9; }`
- **Status tags:** Use inline bold with colored backgrounds — green `#2E7D32` for Live/Resolved, blue `#1565C0` for Happy, dark slate `#2C3E50` for ICP.
- **Severity colors:** Red `#D63B2F` for URGENT/P0, orange `#E65100` for HIGH/Overdue, amber `#F9A825` for MEDIUM. Only use red for inline severity/risk callouts, never for headings.
- **Body font:** Arial, `color: #333`.
- **Links:** Inline with descriptive text.
- **Dividers:** `<hr>` between major sections.
- **Footer:** `color: #999; font-size: 11px; text-align: center;` with "Generated by Claude Agent | [date] | Pathfinder Account Management".

**Structure pattern for dossiers/reports:**

1. Title (H1) with summary metadata table immediately below
2. Sections (H2) each with a proper HTML `<table>` or `<ul>` — never plain text tables
3. Use numbered tables for ordered items (opportunities, feedback) and key-value tables for details
4. Action items in tables with Owner, Due, and color-coded Status columns

---

## Key Folders


| Name                 | Folder ID                           | Location |
| -------------------- | ----------------------------------- | -------- |
| 2026                 | `1xPRPSJUWBtJDbeISgOxJiTX0Y8znczf_` | My Drive |
| mx deep dives        | `1LC-N9ib_c43jJeXkbRm0iO_3FswL-wrn` | 2026/    |
| support intelligence | `12HiJU4UPLifS11vy8066LmnYBR9LK5z8` | 2026/    |
| Weekly Mind Maps 2026 | `1aUdFtQBQ3MsAh1gK6qENFcv0YlYBUCmI` | 2026/    |
| Account Management   | `1-ZfbMtwlJaj-6Hx2LqrTIysvPNxMF7MK` | My Drive |


---

## Workspace Structure

```
launchpad/
  CLAUDE.md              — This file
  .claude/commands/      — Slash command definitions
  .claude/agents/        — Agent definitions (subprocesses)
  .claude/settings.local.json — MCP tool permissions
  scripts/               — Automation scripts (daily-briefing.sh)
  logs/                  — Automation logs (gitignored)
  credentials/           — OAuth tokens and secrets (gitignored)
  projects/              — Sub-projects built from this workspace
```

