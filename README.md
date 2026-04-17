# Launchpad

A Claude Code workspace template for operations and account management teams. MCP-powered, with slash commands, parallel sub-agents, and automated Google Doc output.

This repo turns Claude Code into a full command center — connecting your email, calendar, spreadsheets, Slack, support tools, and data warehouse into a single conversational interface with reusable skills and autonomous agents.

---

## Architecture

```
launchpad/
├── CLAUDE.md                    # The brain: your role, rules, domain knowledge, tool configs
├── .mcp.json                    # MCP server declarations
├── .claude/
│   ├── commands/                # Slash commands (/daily-brief, /mx-lookup, etc.)
│   ├── agents/                  # Autonomous sub-agent definitions
│   └── settings.local.json     # Tool permission allow-list
├── credentials/                 # OAuth secrets (gitignored)
└── projects/                    # Output directory for generated reports
```

| Component | What It Does |
|-----------|-------------|
| `CLAUDE.md` | Your identity, terminology, rules, MCP tool docs, spreadsheet IDs, SQL queries, formatting guides. Claude reads this on every conversation. |
| `.claude/commands/` | Slash commands — each `.md` file defines a reusable skill with step-by-step instructions, tool calls, and output templates. |
| `.claude/agents/` | Agent definitions — each `.md` file defines an autonomous subprocess with its own model, sub-agents, and Google Doc output. |
| `.mcp.json` | Declares which MCP servers to connect. Project-local config. |
| `.claude/settings.local.json` | Auto-approves tool calls matching these patterns so you don't get prompted constantly. |
| `credentials/` | OAuth client secrets and cached tokens. Never committed. |

---

## Prerequisites

- **[Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code)** — `npm install -g @anthropic-ai/claude-code`
- **Node.js 18+** / npm — required for `npx` MCP servers
- **Python 3.10+** — required for `uvx` MCP servers
- **[uv](https://docs.astral.sh/uv/)** — Python package runner (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- **[devbox](https://www.jetpack.io/devbox/)** (optional) — reproducible dev environment

---

## Quick Start

### 1. Fork & Clone

```bash
git clone https://github.com/YOUR_USERNAME/launchpad.git
cd launchpad
```

### 2. Set Up MCP Servers

Add your MCP servers to the Claude Code project. Each server connects a different service:

```bash
# Google Workspace (Gmail, Calendar, Sheets, Drive, Docs)
claude mcp add google-workspace -- uvx workspace-mcp

# Gemini (search, research, image/video gen, document analysis)
claude mcp add gemini -- npx -y @rlabs-inc/gemini-mcp

# Nanobanana (Gemini-powered image generation)
claude mcp add nanobanana -- uvx nanobanana-mcp-server@latest

# Intercom (support conversations)
# Already declared in .mcp.json — just needs OAuth on first use
```

For **Slack** and **data warehouse** connections, configure via Claude Code's global MCP settings or your organization's MCP gateway.

### 3. Add Credentials

```bash
mkdir -p credentials
```

**Google Workspace:** Download your OAuth client secret JSON from [Google Cloud Console](https://console.cloud.google.com/apis/credentials) and place it in `credentials/`. The first Google Workspace tool call will open a browser for OAuth consent.

**Gemini:** Set your API key as an environment variable:
```bash
export GEMINI_API_KEY="your-key-here"
```

**Slack / Intercom:** OAuth flows trigger automatically on first tool call (browser popup).

### 4. Customize CLAUDE.md

This is the most important step. Open `CLAUDE.md` and replace everything with your own context:

```markdown
# Your Workspace Name

## About Me
- Name, role, team, email, timezone

## What I Work On
- Your responsibilities and workflows

## Terminology
- Domain-specific terms your team uses

## MCP Servers & Tools
- Document each server and its key tools

## Key Spreadsheets / Data Sources
- IDs, URLs, and what each contains

## Rules
- How you want Claude to behave

## Skills
- Table of your slash commands

## Agents
- Table of your agent definitions
```

See the existing `CLAUDE.md` for a fully built-out example.

### 5. Update Tool Permissions

Edit `.claude/settings.local.json` to match your MCP server namespaces:

```json
{
  "permissions": {
    "allow": [
      "mcp__google-workspace__*",
      "mcp__slack__*",
      "mcp__your-server__*",
      "WebSearch",
      "WebFetch"
    ]
  }
}
```

### 6. Run Your First Command

```bash
cd launchpad
claude
```

Then try a slash command like `/gcal-today` or ask Claude to run an agent.

---

## MCP Servers

| Server | Connects To | Setup | Auth |
|--------|------------|-------|------|
| `google-workspace` | Gmail, Calendar, Sheets, Drive, Docs | `uvx workspace-mcp` (stdio) | OAuth (browser popup, then cached) |
| `slack` | Slack channels, search, messaging | HTTP/OAuth (global) | OAuth |
| `ask-data-ai` | Snowflake / data warehouse | HTTP (global) | Org-internal |
| `nanobanana` | Gemini image generation | `uvx nanobanana-mcp-server@latest` (stdio) | API key |
| `gemini` | Gemini search, research, video, docs | `npx @rlabs-inc/gemini-mcp` (stdio) | API key |
| `intercom` | Support conversations & contacts | `npx mcp-remote https://mcp.intercom.com/mcp` (stdio) | OAuth (Cloudflare bridge) |

You don't need all of these. Use only the servers relevant to your workflow. Add new ones for Jira, Linear, Notion, Salesforce, or any service with an MCP server.

---

## Commands (Slash Skills)

Each file in `.claude/commands/` defines a reusable skill invoked with `/command-name`.

| Command | Purpose |
|---------|---------|
| `/daily-brief` | Morning briefing: volume alerts + calendar + email + support |
| `/gcal-today` | Show today's calendar and upcoming meetings |
| `/gmail-search` | Search Gmail inbox |
| `/gdrive-search` | Search Google Drive for files |
| `/slack-search` | Search Slack messages and channels |
| `/slack-send` | Compose and send a Slack message |
| `/data-query` | Query data warehouse via ask-data-ai |
| `/mx-lookup` | Cross-reference a merchant across all data sources |
| `/call-prep` | Prepare for a merchant call with full context |
| `/intercom` | Check Intercom inbounds or search support history |
| `/support-scan` | Combined support scan: Slack + Intercom + pattern alerts |
| `/support-intel` | Support pattern analysis: repeat issues, risk flags |
| `/weekly-recap` | Weekly summary across all tools |
| `/card-metrics` | Card volume metrics with period-over-period changes |
| `/feedback-log` | Log product feedback to a tracker |
| `/location-scout` | 360° location analysis: demographics, competition, traffic drivers |

### Command File Format

```markdown
# /command-name — Short Description

Description of what this command does.

## Instructions

### Step 1: Do Something
Use `mcp__server__tool_name` with these parameters...

### Step 2: Present Results
Format the output like this...

## Output Format
[markdown template]

## Examples
/command-name argument
/command-name different argument
```

---

## Agents

Each file in `.claude/agents/` defines an autonomous subprocess that runs in isolation (optionally in the background). Agents can spawn their own sub-agents for parallel execution.

| Agent | Trigger | What It Does |
|-------|---------|-------------|
| `mx-researcher` | "Research [merchant]" | Comprehensive merchant dossier from 9+ data sources. Outputs Google Doc. |
| `briefing-compiler` | "Compile my morning brief" | Multi-source daily/weekly briefing. Ideal for background execution. |
| `support-intel` | "Run a deep support analysis" | Pattern detection across support conversations. Produces report. |
| `qbr-generator` | "Generate a QBR for [merchant]" | Full quarterly review via 4 parallel sub-agents. Outputs .md + Google Doc. |
| `location-scout` | "Research [address] for [cuisine]" | 360° location research via 4 parallel sub-agents. Demographics + competition + traffic drivers + marketplace data. |

### Agent File Format

```yaml
---
name: agent-name
description: |
  When to use this agent and what it does.

  <example>
  Context: Description of the scenario
  user: "User's trigger phrase"
  assistant: "How Claude dispatches this agent"
  </example>

model: opus    # opus | sonnet | haiku
color: blue    # for visual identification
---

You are an expert [role]. Your job is to [purpose].

## Step 1: Parse Input
...

## Step 2: Launch Sub-Agents (if parallel)
Send a SINGLE message with multiple Task tool calls...

## Step 3: Synthesize Results
...

## Step 4: Create Google Doc
Use `import_to_google_doc` with `source_format: "html"`...
```

---

## Customizing for Your Role

### What to Change

| File | What to Customize |
|------|------------------|
| `CLAUDE.md` | Your name, email, timezone, role, team, terminology, rules, spreadsheet IDs, Slack channel IDs, data table references, formatting preferences |
| `.mcp.json` | Add/remove MCP servers for your tool stack |
| `.claude/settings.local.json` | Update permission patterns to match your MCP namespaces |
| `.claude/commands/*.md` | Edit existing or create new slash commands for your workflows |
| `.claude/agents/*.md` | Edit existing or create new agents for your use cases |
| `credentials/` | Your own OAuth client secrets and API keys |

### Tips

- **Start with CLAUDE.md.** It's the single most important file. Claude reads it on every conversation and follows it as law.
- **Be specific in rules.** "Always include the Store ID" is better than "be thorough." Specific rules produce specific behavior.
- **Hardcode IDs.** Spreadsheet IDs, Slack channel IDs, folder IDs — put them directly in command files so Claude doesn't have to look them up every time.
- **Use the agent pattern for heavy workflows.** If a task needs 3+ data sources or produces a document, make it an agent with parallel sub-agents.
- **Test commands iteratively.** Run a command, see what's off, edit the `.md` file, run again. The feedback loop is fast.

---

## How It Works

1. **You type** a natural language request or slash command
2. **Claude reads** `CLAUDE.md` for context, rules, and tool documentation
3. **Claude executes** the matching command or dispatches an agent
4. **MCP servers** handle the actual API calls (Gmail, Slack, Snowflake, etc.)
5. **Results** come back as formatted markdown or a Google Doc link

For agents with sub-agents (like `qbr-generator` or `location-scout`), the orchestrator launches multiple Task sub-processes in parallel, each querying different data sources, then synthesizes everything into a single output.

---

## License

MIT
