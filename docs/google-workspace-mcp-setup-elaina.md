# Google Workspace MCP Setup for Claude Code

> Connect Gmail, Calendar, Drive, Sheets, and Docs to Claude Code through a single MCP server. ~80+ tools, one setup.

**Package:** [`workspace-mcp`](https://github.com/taylorwilsdon/google_workspace_mcp) by Taylor Wilsdon
**Docs:** [workspacemcp.com](https://workspacemcp.com)

---

## What You'll Get

Once set up, you can ask Claude things like:
- "Check my calendar for today"
- "Search my Gmail for emails from [person] this week"
- "Read the spreadsheet [name or URL]"
- "Search my Drive for [file name]"
- "Draft an email to [person] about [topic]"
- "What's on my calendar tomorrow?"
- "Summarize the last 5 emails in this thread"

Claude gets direct access to your Google Workspace — no copy-pasting, no switching tabs.

---

## Prerequisites

| Requirement | How to check / install |
|-------------|----------------------|
| **Claude Code** | You should already have the `claude` CLI installed. Run `claude --version` to confirm. |
| **Python 3.11+** | Run `python3 --version`. If missing or below 3.11, install from [python.org](https://www.python.org/downloads/). |
| **uv** (Python package runner) | Run `uvx --version`. If missing, install: `curl -LsSf https://astral.sh/uv/install.sh \| sh` then restart your terminal. |
| **Google Workspace account** | Your `elaina.atallah@doordash.com` email. |

---

## Step 1: Create Google Cloud OAuth Credentials

This is the longest step, but you only do it once.

### 1a. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Sign in with your **DoorDash Google account** (`elaina.atallah@doordash.com`)
3. Click the project dropdown (top-left, next to "Google Cloud") → **New Project**
4. Name it something like `Claude MCP` → **Create**
5. Make sure that project is selected in the dropdown

### 1b. Enable the APIs

1. In the left sidebar: **APIs & Services → Library**
2. Search for and **Enable** each of these (click into each one and hit "Enable"):
   - **Gmail API**
   - **Google Calendar API**
   - **Google Drive API**
   - **Google Sheets API**
   - **Google Docs API**

### 1c. Set Up OAuth Consent Screen

1. In the left sidebar: **APIs & Services → OAuth consent screen**
2. Choose **Internal** (this should be available since we're on a Google Workspace org)
   - If Internal isn't available, choose **External** and add your email as a test user later
3. Fill in:
   - **App name:** `Claude MCP` (or whatever you want)
   - **User support email:** your email
   - **Developer contact:** your email
4. Click through the remaining screens (Scopes, Test Users) — you can leave defaults
5. **Save and Continue** through to the end

### 1d. Create OAuth Credentials

1. In the left sidebar: **APIs & Services → Credentials**
2. Click **+ Create Credentials** → **OAuth Client ID**
3. **Application type:** `Desktop Application`
4. **Name:** `Claude MCP` (or whatever)
5. Click **Create**
6. You'll see a popup with your **Client ID** and **Client Secret** — **copy both** and save them somewhere safe (you'll need them in Step 2)

> The Client ID looks like: `123456789-abcdefg.apps.googleusercontent.com`
> The Client Secret looks like: `GOCSPX-abcdefghijk`

---

## Step 2: Add the MCP Server to Claude Code

Open your terminal, `cd` into your Claude Code project directory, and run this command (replace the two placeholder values with your actual credentials from Step 1):

```bash
claude mcp add google-workspace \
  -e GOOGLE_OAUTH_CLIENT_ID=YOUR_CLIENT_ID_HERE \
  -e GOOGLE_OAUTH_CLIENT_SECRET=YOUR_CLIENT_SECRET_HERE \
  -- uvx workspace-mcp
```

That's it. This registers the server with Claude Code.

### Verify it was added

Run `claude mcp list` — you should see `google-workspace` in the output.

---

## Step 3: Authenticate (First Run)

1. Start Claude Code: just type `claude` in your terminal
2. Ask it something that uses Google, like: **"What's on my calendar today?"**
3. Claude will tell you it needs to authenticate — a **browser window** will open
4. Sign in with `elaina.atallah@doordash.com` and **grant all permissions**
5. The browser will say "Authentication successful" — go back to your terminal
6. Claude will now complete your request

> **The token is cached locally** — you won't need to re-authenticate unless it expires (rare). If it does, just repeat this step.

---

## Step 4: Tell Claude Your Email

Every Google Workspace tool call needs your email address. Add this to your project's `CLAUDE.md` file so Claude always knows:

```markdown
## Rules
- Always pass `user_google_email: "elaina.atallah@doordash.com"` to every google-workspace tool call. No exceptions.
```

Without this, Claude will ask you for your email on every Google-related request.

---

## Step 5: Auto-Allow Tools (Optional but Recommended)

By default, Claude will ask your permission every time it tries to use a Google tool. To skip the prompts, create or edit `.claude/settings.local.json` in your project root:

```json
{
  "permissions": {
    "allow": [
      "mcp__google-workspace__*"
    ]
  }
}
```

This auto-allows all Google Workspace tools. If you want to be more selective (e.g., allow reads but require approval for sends), you can list specific tools instead:

```json
{
  "permissions": {
    "allow": [
      "mcp__google-workspace__search_gmail_messages",
      "mcp__google-workspace__get_gmail_message_content",
      "mcp__google-workspace__get_gmail_thread_content",
      "mcp__google-workspace__get_events",
      "mcp__google-workspace__read_sheet_values",
      "mcp__google-workspace__search_drive_files",
      "mcp__google-workspace__get_drive_file_content",
      "mcp__google-workspace__get_doc_content"
    ]
  }
}
```

---

## You're Done!

Test it out:
- `"Check my calendar for today"`
- `"Search my Gmail for emails from Phil this week"`
- `"Find the Master Hub spreadsheet in my Drive"`
- `"Read the first sheet of [spreadsheet URL]"`

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `uvx: command not found` | Install uv: `curl -LsSf https://astral.sh/uv/install.sh \| sh` then restart terminal |
| OAuth popup doesn't open | Make sure `GOOGLE_OAUTH_CLIENT_ID` and `GOOGLE_OAUTH_CLIENT_SECRET` are correct. Run `claude mcp list` to verify they're set. |
| "API not enabled" error | Go back to Google Cloud Console → APIs & Services → Library → enable the specific API it's complaining about |
| "Access blocked" or "App not verified" | If you chose External in Step 1c, make sure your email is added as a test user in the OAuth consent screen |
| Token expired | Delete `~/.workspace-mcp/` folder (or wherever tokens are cached) and re-authenticate |
| Claude doesn't know my email | Add the `user_google_email` rule to your CLAUDE.md (Step 4) |
| MCP server not connecting | Run `claude mcp list` to check status. Try `claude mcp remove google-workspace` then re-add it (Step 2). |

---

## Quick Reference

| What | Value |
|------|-------|
| MCP Package | `workspace-mcp` (via `uvx`) |
| Your email | `elaina.atallah@doordash.com` |
| GitHub | https://github.com/taylorwilsdon/google_workspace_mcp |
| Docs | https://workspacemcp.com |
| Tool count | ~80+ across Gmail, Calendar, Drive, Sheets, Docs |
