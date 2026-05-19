# Launchpad — Phil's Homebase

> Command center for Pathfinder Account Management.

---

## About Me

- **Name:** Philip Bornhurst (Phil)
- **Role:** Head of Account Management for Pathfinder, Strategy and Operations team at DoorDash Commerce Platform
- **Email:** philip.bornhurst@doordash.com
- **Timezone:** America/Los_Angeles
- **Team:** One direct report — Mallory Thornley (Account Manager)

## What I Work On

- mx relationships for Pathfinder (DoorDash's POS product) — account health, calls, MSAT, escalations, QBRs
- Product feedback collection + tracking
- Sales → Launch → AM handoffs (Launch hands off post go-live)
- Strategic adoption: Gift Cards, Kiosk, OCL, Mobile App, 1p Online Ordering

---

## Terminology

| Term | Meaning |
| ---- | ------- |
| mx   | Merchant (always lowercase) |
| POS  | Point of Sale |
| GOV  | Gross Order Value |
| QBR  | Quarterly Business Review |
| MSAT | Merchant Satisfaction Score |
| ICP  | Ideal Customer Profile (highest priority tier) |
| OCL  | Omni-Channel Loyalty |
| 1p   | First-party (online ordering) |
| OSW  | Orders per Store Week |
| AM   | Account Manager |
| DRI  | Directly Responsible Individual |
| xfn  | Cross-functional |
| SIT  | Support Intelligence Tracker |
| Puck / M2 | Stripe M2 card reader — current hardware, replacing Wise |
| Wise | WisePOS card reader — legacy, being phased out |
| CFD  | Customer-Facing Display |

---

## Communication Style

- **Slack:** direct, concise, action-oriented. Use mx names + Store IDs.
- **Emails:** professional but warm with mx; data-driven internally.
- **Call notes:** bullet-heavy with action items, MSAT scores, follow-up dates.
- **Avoid:** over-explanation, consultant speak, asking permission for routine tasks. Default to action.

---

## Rules

1. **Default to action** — "Check emails" means fetch them immediately, don't ask.
2. **Cross-reference everything** — For mx questions, pull Master Hub + running notes + support + volume.
3. **Exact filtering** — Use EXACT matches for Account Manager / Status / any column. No approximating.
4. **Volume alerts** — Prioritize mx who went dark (previous > 0, current = 0/null).
5. **Always include Store ID + merchant portal link** when referencing a mx.
6. **Use "mx"** lowercase. Always.
7. **Show your work** — State filters explicitly: "Filtering for: Account Manager = 'Phil Bornhurst' AND Status = 'Live'"
8. **google-workspace email** — Every google-workspace call requires `user_google_email: "philip.bornhurst@doordash.com"`. No exceptions.
9. **Gmail rate limits** — Calendar before gmail. One gmail read per batch.
10. **Confirm before sending** — Never send Slack/email or modify spreadsheet data without explicit approval. Draft first.
11. **Timezone** — America/Los_Angeles unless specified.
12. **Day of week** — Always compute programmatically (`date -j -f "%Y-%m-%d" "YYYY-MM-DD" "+%A"`). Never guess.

---

## MCP Gotchas

The runtime injects the tool catalog each session. These are the non-obvious rules:

- **Slack `oldest` / `latest`** — Unix epoch seconds, NOT date strings. `"2026-02-14"` silently fails (returns from beginning of channel). Compute first: `date -j -f "%Y-%m-%d %H:%M:%S" "2026-02-14 00:00:00" "+%s"`.
- **Slack workflow bots** — Pass `include_bots: true` to find install/check-in reports in #pathfinder-mxonboarding.
- **Snowflake routing** — Default to `ask-data-ai` (`ask_firefly`, `search_data_catalog`, `DescribeTable`, `ask_data_mx`, `ask_finance_ai`, etc.) — fast, no OAuth drops. Fall back to **direct Snowflake** (`python3 scripts/snowflake_query.py --json "SQL"`) for: audit tables, wide scans >30d, queries expected >30s. `mcp__ask-data-ai__ExecuteSnowflakeQuery` drops every ~2min ("Downstream not connected").
- **Glean** — Keyword search only (2–5 keywords, no full sentences, no booleans). `mcp__claude_ai_Glean__search` first, then `read_document` for full content.

Key Slack channels: #pathfinder-support (C067SSZ1AMT), #pathfinder-mxonboarding (C067E67HNAZ), #phils-gumloop-agent (C0AC2NK50QN — posting/test).

---

## Key Spreadsheets

| Name | ID | Primary Sheet |
| ---- | -- | ------------- |
| Master Hub | `1ndVs2lPhS5frpkEV0KzK7ec5aS18fmr9h1BQEu099E4` | (default — IMPORTRANGE view) |
| Product Feedback Tracker | `1-EylRCLxhpStfEoj-8ga9Ex_26dHBoWgxU6Yr_hT0Y4` | The Final Final Boss |
| Volume Drop Data | `1bu0fWwKWQQeI8nrkhGKA68dTzKRtIh_MXAPeqze0NX0` | (default) |
| Support Intelligence Tracker | `1XduutDkGbvZpe9kGyoW9d1_zW08iHxFnVzxxltP7w5U` | Conversation Log |
| Growth Advisory Ledger | `1uS_noBD2nTYjpM6VJvIQwSLMKA_tLkiyo-3dHwi0Ta8` | Log |

## Key Folders

| Name | Folder ID | Location |
| ---- | --------- | -------- |
| 2026 | `1xPRPSJUWBtJDbeISgOxJiTX0Y8znczf_` | My Drive — internal/leadership docs |
| mx deep dives | `1LC-N9ib_c43jJeXkbRm0iO_3FswL-wrn` | 2026/ |
| support intelligence | `12HiJU4UPLifS11vy8066LmnYBR9LK5z8` | 2026/ |
| Weekly Mind Maps 2026 | `1aUdFtQBQ3MsAh1gK6qENFcv0YlYBUCmI` | 2026/ |
| benchmarking | (auto-created on first /benchmark-doc run) | 2026/ |
| Account Management | `1-ZfbMtwlJaj-6Hx2LqrTIysvPNxMF7MK` | My Drive — **SHARED, team-visible** |

---

## Key Snowflake Tables

Tables I touch directly. Agent-specific tables (ads, geo-cuisine, menu performance, etc.) are documented inside the agent files that use them.

| Table | What |
| ----- | ---- |
| `edw.pathfinder.agg_pathfinder_stores_daily` | Daily per-store card volume + GOV. Core Pathfinder metrics. |
| `edw.merchant.fact_merchant_sales` | Near-realtime order-level (~minutes latency). POS channels = `channel IN ('In-store', 'Kiosk')`. Used by mx-alert-monitor. |
| `edw.merchant.fact_merchant_transactions_details_portal` | Financial detail (subtotal, fees, commissions, discounts) by channel. **Critical:** In-store/Kiosk = `final_order_status = 'Picked Up'`. Always filter `IN ('Delivered', 'Picked Up')`. |
| `proddb.public.pathfinder_merchant_database_from_gsheet_cleaned` | Mx lifecycle dates: CW date, OB call date. |

**POS Cohort Query:** Canonical per-mx lifecycle + performance SQL at [`docs/queries/pos-cohort.sql`](docs/queries/pos-cohort.sql). Filter `WHERE pf.store_id = [STORE_ID]` to scope to one mx.

---

## Support Channels

- **Intercom** — primary inbound. ALL mx support texts. High volume.
- **#pathfinder-support** — escalation layer; critical/novel only.
- **#pathfinder-mxonboarding** — onboarding, installs, launcher visits. Workflow bots post here (`include_bots: true`).
- **Launcher reports** — Gmail label `Launcher Reports`, not Slack.
- Cross-reference Intercom contacts to Master Hub by name/phone/email (Intercom doesn't always show business name).

---

## Merchant Tiers

ICP > Tier 1 > Tier 2 > Tier 3. Extra attention on ICP + Tier 1 for proactive outreach and issue resolution.

---

## Daily Briefing & Monitoring

- **Daily brief:** `/daily-brief` — `briefing-compiler` agent (4 parallel sub-agents). HTML email + Slack to #phils-gumloop-agent. launchd fires `scripts/daily-briefing.sh` at 8am daily. Each sub-agent degrades independently if a source fails.
- **Intraday alerts:** launchd fires `scripts/mx-alert-monitor.sh` 3x daily (10:30 / 14:30 / 17:30 PST). `fact_merchant_sales` vs same window last week. POS dark + Marketplace active = HIGH alarm.
- **Ad-hoc:** `/mx-alert-monitor` (single check), `/churn-risk` (full health doc).

---

## Skills & Agents

- **Skills (slash commands):** defined in `.claude/commands/`. The runtime injects the list each session — invoke via `/<name>` or natural language. Read the matching `.md` file for behavior.
- **Agents (subprocess workers):** defined in `.claude/agents/`. Trigger by describing the task or "Run [name] agent"; add "in the background" to keep working in parallel. Read the agent `.md` file for trigger phrases and inputs.

---

## Google Docs Formatting

When creating Google Docs, use `import_to_google_doc` with `source_format: "html"`. Never `create_doc` with plain text.

- **Headings:** `#2C3E50` (H1/H2), `#34495E` (H3). No red in titles.
- **Table headers:** `background-color: #2C3E50; color: white;`
- **Alternating rows:** `tr:nth-child(even) { background-color: #f9f9f9; }`
- **Status tags:** green `#2E7D32` Live/Resolved, blue `#1565C0` Happy, dark slate `#2C3E50` ICP.
- **Severity:** red `#D63B2F` URGENT/P0, orange `#E65100` HIGH/Overdue, amber `#F9A825` MEDIUM. Red ONLY inline for severity — never in headings.
- **Body:** Arial, `color: #333`. **Dividers:** `<hr>` between sections.
- **Footer:** `color: #999; font-size: 11px; text-align: center;` — "Generated by Claude Agent | [date] | Pathfinder Account Management".
- **Structure:** H1 title → metadata table → H2 sections with real `<table>` or `<ul>` (never plain text tables) → action items with Owner / Due / color-coded Status.

---

## Help Center Grounding (email-triage and product Qs)

**Pathfinder POS topics** — ground in the local Zendesk mirror:
- **Lookup:** `python3 scripts/help_center_lookup.py --top 5 "query"` → ranked JSON.
- **Refresh:** weekly via launchd (`scripts/refresh-help-center.sh`, Mon 7am PST). Manual: `python3 scripts/scrape_zendesk_help_center.py`.
- **Map files:** `data/help-center-map.json` + `data/help-center-map.md`.
- **Drafting rule:** NEVER fabricate product answers. Run lookup → cite article URL on its own line ("More detail: <URL>") → if no confident match, write "checking with the team."

**Everything else** (Marketplace, Storefront, promos, ratings, policy, internal process) — ground in **Glean** via `mcp__claude_ai_Glean__search`. Only cite externally-accessible URLs to mx; for internal-only sources, omit URL and offer to share guidance separately.

---

## Workspace Structure

```
launchpad/
  CLAUDE.md
  .claude/commands/      — Slash command (skill) definitions
  .claude/agents/        — Agent definitions
  .claude/settings.local.json — MCP tool permissions
  scripts/               — Automation scripts (daily-briefing.sh, snowflake_query.py, help_center_lookup.py, …)
  docs/queries/          — Canonical SQL (pos-cohort.sql, …)
  data/                  — Generated reference data (help-center-map.json, …)
  logs/                  — Automation logs (gitignored)
  credentials/           — OAuth tokens (gitignored)
  .email-triage/         — /email-triage run state (gitignored)
  projects/              — Sub-projects
```

---

## Key Links

- **Master Hub:** https://docs.google.com/spreadsheets/d/1ndVs2lPhS5frpkEV0KzK7ec5aS18fmr9h1BQEu099E4/edit
- **Product Feedback Tracker:** https://docs.google.com/spreadsheets/d/1-EylRCLxhpStfEoj-8ga9Ex_26dHBoWgxU6Yr_hT0Y4/edit
- **Volume Drop Data:** https://docs.google.com/spreadsheets/d/1bu0fWwKWQQeI8nrkhGKA68dTzKRtIh_MXAPeqze0NX0/edit
- **Merchant Portal:** `https://www.doordash.com/merchant/sales?store_id=[STORE_ID]`
