# Launchpad — Phil's Homebase

> Command center for Pathfinder Account Management. All MCP tools, all workflows, one workspace.

---

## About Me

- **Name:** Philip Bornhurst (Phil)
- **Role:** Head of Account Management for Pathfinder, Strategy and Operations team at DoorDash Commerce Platform
- **Email:** philip.bornhurst@doordash.com
- **Timezone:** America/Los_Angeles (PST/PDT)
- **Team:** One direct report — Mallory Thornley (Account Manager)

---

## What I Work On

- **Account Management:** Managing mx relationships for Pathfinder (DoorDash's POS product)
- **Account Health:** Monitor volume trends, account status, merchant satisfaction (MSAT scores)
- **Merchant Calls:** Intro calls, check-ins, QBRs with restaurant partners
- **Product Feedback:** Collect and track mx feature requests and pain points
- **Support Escalations:** Handle escalated issues from #pathfinder-support and Intercom
- **Sales Handoffs:** Onboard new mx from sales team, coordinate go-live
- **Strategic Initiatives:** Drive adoption of ancillary products (Gift Cards, Kiosk, OCL, Mobile App, 1p Online Ordering)

---

## Terminology

| Term | Meaning |
|------|---------|
| mx | Merchant (always lowercase) |
| POS | Point of Sale |
| GOV | Gross Order Value |
| QBR | Quarterly Business Review |
| MSAT | Merchant Satisfaction Score |
| ICP | Ideal Customer Profile (highest priority tier) |
| OCL | Omni-Channel Loyalty |
| 1p | First-party (online ordering) |
| OSW | Order Success Widget |
| AM | Account Manager |
| DRI | Directly Responsible Individual |
| xfn | Cross-functional |

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
- **Key channels:**
  - #pathfinder-support (C067SSZ1AMT) — escalations
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

---

## Key Spreadsheets

| Name | Spreadsheet ID | Primary Sheet |
|------|---------------|---------------|
| Master Hub | `1ndVs2lPhS5frpkEV0KzK7ec5aS18fmr9h1BQEu099E4` | (default) |
| Product Feedback Tracker | `1-EylRCLxhpStfEoj-8ga9Ex_26dHBoWgxU6Yr_hT0Y4` | The Final Final Boss |
| Volume Drop Data | `1bu0fWwKWQQeI8nrkhGKA68dTzKRtIh_MXAPeqze0NX0` | (default) |

---

## Merchant Tiers (Priority Order)

1. **ICP** — Ideal Customer Profile (highest priority)
2. **Tier 1** — High-impact mx
3. **Tier 2** — Mid-tier accounts
4. **Tier 3** — Standard accounts

Focus extra attention on ICP and Tier 1 for proactive outreach and issue resolution.

---

## Key Links

- **Master Hub:** https://docs.google.com/spreadsheets/d/1ndVs2lPhS5frpkEV0KzK7ec5aS18fmr9h1BQEu099E4/edit
- **Product Feedback Tracker:** https://docs.google.com/spreadsheets/d/1-EylRCLxhpStfEoj-8ga9Ex_26dHBoWgxU6Yr_hT0Y4/edit
- **Volume Drop Data:** https://docs.google.com/spreadsheets/d/1bu0fWwKWQQeI8nrkhGKA68dTzKRtIh_MXAPeqze0NX0/edit
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

- **Command:** `/daily-brief` or "Generate daily briefing"
- **Post to:** #phils-gumloop-agent (C0AC2NK50QN)
- **Sections:** Volume Alerts → Today's Calendar → Email Summary → Support Escalations → Action Items
- **Timing:** Designed for 6-7am PST before my workday starts

---

## Skills

| Command | Purpose |
|---------|---------|
| `/daily-brief` | Morning briefing: volume alerts + calendar + email + support |
| `/gcal-today` | Show today's calendar and upcoming meetings |
| `/gmail-search` | Search Gmail inbox |
| `/gdrive-search` | Search Google Drive for files |
| `/slack-search` | Search Slack messages and channels |
| `/slack-send` | Compose and send a Slack message |
| `/data-query` | Query DoorDash data warehouse via ask-data-ai |
| `/mx-lookup` | Cross-reference a mx across all data sources |
| `/call-prep` | Prepare for a mx call with full context |
| `/volume-alert` | Check for volume drops and mx going dark |
| `/support-scan` | Scan #pathfinder-support for recent escalations |
| `/weekly-recap` | Weekly summary across all tools |
| `/feedback-log` | Log product feedback to the tracker |

---

## Agents

Agents run as isolated subprocesses — they pull from multiple data sources in their own context and return a polished result. They can run in the **background** while you keep working.

| Agent | Trigger | What it does |
|-------|---------|-------------|
| `mx-researcher` | "Research [mx]", "Deep dive on [mx]", "Give me everything on [mx]" | Comprehensive mx dossier: Master Hub + Volume + Slack + Email + Feedback + Running Notes + Snowflake. Auto-creates a formatted Google Doc in the `mx deep dives` folder and shares with doordash.com. |
| `briefing-compiler` | "Compile my morning brief", "Run my daily brief in the background" | Polished daily/weekly briefing compiled from all sources. Ideal for background execution. |

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

| Name | Folder ID | Location |
|------|-----------|----------|
| 2026 | `1xPRPSJUWBtJDbeISgOxJiTX0Y8znczf_` | My Drive |
| mx deep dives | `1LC-N9ib_c43jJeXkbRm0iO_3FswL-wrn` | 2026/ |

---

## Workspace Structure

```
launchpad/
  CLAUDE.md              — This file
  .claude/commands/      — Slash command definitions
  .claude/agents/        — Agent definitions (subprocesses)
  .claude/settings.local.json — MCP tool permissions
  credentials/           — OAuth tokens and secrets (gitignored)
  projects/              — Sub-projects built from this workspace
```
