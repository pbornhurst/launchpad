# Google Workspace MCP Setup Guide

> One MCP server for Gmail, Calendar, Drive, Sheets, and Docs — ~80+ tools through a single connection.

**Package:** [`workspace-mcp`](https://github.com/taylorwilsdon/google_workspace_mcp) by Taylor Wilsdon
**Docs:** [workspacemcp.com](https://workspacemcp.com)

---

## Prerequisites

- **Claude Code** installed (`claude` CLI)
- **Python 3.11+** and **uv/uvx** ([install uv](https://docs.astral.sh/uv/getting-started/installation/))
- A **Google Workspace** account (DoorDash email)

---

## Step 1: Create Google Cloud OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. **Enable APIs** — go to **APIs & Services → Library** and enable:
   - Gmail API
   - Google Calendar API
   - Google Drive API
   - Google Sheets API
   - Google Docs API
   - *(Optional: Slides, Forms, Tasks, People API, Chat if you want those too)*
4. **Set up OAuth consent screen:**
   - Go to **APIs & Services → OAuth consent screen**
   - Choose **Internal** (if available for your org) or **External**
   - Fill in app name (e.g., "Claude Workspace MCP"), support email, etc.
   - Add your email to test users if using External
5. **Create credentials:**
   - Go to **APIs & Services → Credentials**
   - Click **Create Credentials → OAuth Client ID**
   - Application type: **Desktop Application**
   - Name it whatever you want (e.g., "Claude MCP")
   - Click **Create**
6. **Copy your Client ID and Client Secret** — you'll need these in Step 2

---

## Step 2: Add the MCP Server to Claude Code

Open your terminal and `cd` into your Claude Code project directory, then run:

```bash
claude mcp add google-workspace \
  -e GOOGLE_OAUTH_CLIENT_ID=YOUR_CLIENT_ID_HERE \
  -e GOOGLE_OAUTH_CLIENT_SECRET=YOUR_CLIENT_SECRET_HERE \
  -- uvx workspace-mcp --tools gmail calendar drive sheets docs
```

Replace `YOUR_CLIENT_ID_HERE` and `YOUR_CLIENT_SECRET_HERE` with the values from Step 1.

**Or** manually add this to your project's `.claude/settings.local.json` under `mcpServers`:

```json
{
  "google-workspace": {
    "type": "stdio",
    "command": "uvx",
    "args": [
      "workspace-mcp",
      "--tools", "gmail", "calendar", "sheets", "drive", "docs"
    ],
    "env": {
      "GOOGLE_OAUTH_CLIENT_ID": "YOUR_CLIENT_ID_HERE",
      "GOOGLE_OAUTH_CLIENT_SECRET": "YOUR_CLIENT_SECRET_HERE"
    }
  }
}
```

### Tool Selection Options

You can customize which tools load:

| Flag | What it does |
|------|-------------|
| `--tools gmail drive calendar` | Only load specific services |
| `--tool-tier core` | Essential tools only |
| `--tool-tier extended` | Core + additional features |
| `--tool-tier complete` | Everything (all 12 services) |
| `--read-only` | Read-only scopes, no write access |
| `--permissions gmail:readonly drive:full` | Granular per-service permissions |

### Permission Levels (per service)

Gmail supports granular levels: `readonly` → `organize` → `drafts` → `send` → `full` (cumulative).
Other services support: `readonly` or `full`.

Example — read-only Gmail but full Drive access:
```bash
uvx workspace-mcp --permissions gmail:readonly drive:full calendar:full sheets:full docs:full
```

---

## Step 3: Auto-Allow the Tools (Optional)

To avoid permission prompts on every tool call, add this to your project's `.claude/settings.local.json`:

```json
{
  "permissions": {
    "allow": [
      "mcp__google-workspace__*"
    ]
  }
}
```

This wildcards all google-workspace tools. You can also be more specific:
```json
{
  "permissions": {
    "allow": [
      "mcp__google-workspace__search_gmail_messages",
      "mcp__google-workspace__get_gmail_message_content",
      "mcp__google-workspace__get_events",
      "mcp__google-workspace__read_sheet_values",
      "mcp__google-workspace__search_drive_files"
    ]
  }
}
```

---

## Step 4: First Run — Authenticate

1. Start Claude Code in your project: `claude`
2. Ask it to do something with Google (e.g., "check my calendar today")
3. A **browser window** will open for Google OAuth consent
4. Sign in with your Google account and grant permissions
5. The token is cached locally — you won't need to re-auth unless it expires

---

## Step 5: Use It

Every tool call requires `user_google_email` as a parameter. Tell Claude your email or add it to your CLAUDE.md:

```markdown
## Rules
- Always pass `user_google_email: "your.email@doordash.com"` to every google-workspace tool call.
```

### Example prompts:
- "Check my calendar for today"
- "Search my Gmail for emails from [person] this week"
- "Read the spreadsheet [name/ID]"
- "Search my Drive for [file name]"
- "Draft an email to [person] about [topic]"

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `uvx: command not found` | Install uv: `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| OAuth popup doesn't appear | Check that `GOOGLE_OAUTH_CLIENT_ID` and `GOOGLE_OAUTH_CLIENT_SECRET` are set correctly |
| "API not enabled" errors | Go back to Google Cloud Console and enable the specific API |
| Token expired | Delete cached credentials and re-authenticate on next call |
| Read-only access needed | Add `--read-only` flag or use `--permissions gmail:readonly` |

---

## Reference

- **GitHub:** https://github.com/taylorwilsdon/google_workspace_mcp
- **PyPI:** https://pypi.org/project/workspace-mcp/
- **Docs:** https://workspacemcp.com
- **Quick Start:** https://workspacemcp.com/quick-start
