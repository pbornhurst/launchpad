#!/bin/bash
# Daily Briefing Automation
# Invokes Claude CLI headlessly to compile and send the morning briefing.
# Designed for macOS launchd scheduling (8am PST daily).
#
# Usage:
#   ./scripts/daily-briefing.sh          # Run daily briefing
#   ./scripts/daily-briefing.sh weekly   # Run weekly briefing
#
# Prerequisites:
#   - claude CLI installed at /usr/local/bin/claude
#   - MCP servers configured in the launchpad workspace
#   - OAuth tokens valid for Google Workspace, Slack, Intercom

set -euo pipefail

# Configuration
WORKSPACE="/Users/philip.bornhurst/Claude/launchpad"
LOG_DIR="${WORKSPACE}/logs"
CLAUDE_BIN="/usr/local/bin/claude"
DATE=$(date +"%Y-%m-%d")
MODE="${1:-daily}"

# Ensure log directory exists
mkdir -p "${LOG_DIR}"

# Log file for this run
LOG_FILE="${LOG_DIR}/briefing-${MODE}-${DATE}.log"

echo "=== Briefing run started: $(date) ===" >> "${LOG_FILE}"
echo "Mode: ${MODE}" >> "${LOG_FILE}"

# Wait for Tailscale VPN connectivity
# On wake, the Mac may not have VPN up yet. Wait up to 5 minutes.
MAX_WAIT=300
INTERVAL=15
WAITED=0

while ! ifconfig 2>/dev/null | grep -q "inet 100\.\|inet 10\.39\."; do
  if [ ${WAITED} -ge ${MAX_WAIT} ]; then
    echo "ERROR: Tailscale VPN not connected after ${MAX_WAIT}s. Aborting." >> "${LOG_FILE}"
    exit 1
  fi
  echo "Waiting for Tailscale VPN... (${WAITED}s elapsed)" >> "${LOG_FILE}"
  sleep ${INTERVAL}
  WAITED=$((WAITED + INTERVAL))
done
echo "Tailscale VPN connected (waited ${WAITED}s)" >> "${LOG_FILE}"

# MCP warm-up: force Google Workspace MCP server init and OAuth token refresh
# before the main briefing. Uses haiku for speed. Failure here is non-fatal —
# the retry logic below handles persistent MCP issues.
echo "Warming up MCP servers..." >> "${LOG_FILE}"
cd "${WORKSPACE}"
"${CLAUDE_BIN}" \
  --print \
  --dangerously-skip-permissions \
  --model haiku \
  "Use the google-workspace list_calendars tool with user_google_email philip.bornhurst@doordash.com. Just confirm it works." \
  >> "${LOG_FILE}" 2>&1 || echo "WARN: MCP warm-up failed (non-fatal, will retry)" >> "${LOG_FILE}"
echo "MCP warm-up complete." >> "${LOG_FILE}"

# Build the prompt based on mode
if [ "${MODE}" = "weekly" ]; then
  PROMPT="Compile a weekly briefing. Use the briefing-compiler agent in weekly mode. Send the HTML email and Slack summary."
else
  PROMPT="Compile my morning brief. Use the briefing-compiler agent for a daily briefing. Send the HTML email and Slack summary."
fi

# Run Claude in headless mode from the workspace directory
# --print: non-interactive output
# --dangerously-skip-permissions: needed for unattended execution
# --model sonnet: match the agent's model
"${CLAUDE_BIN}" \
  --print \
  --dangerously-skip-permissions \
  --model sonnet \
  "${PROMPT}" \
  >> "${LOG_FILE}" 2>&1

EXIT_CODE=$?

# Detect partial failure: email not sent due to MCP issues
# If detected, wait 60s for transient issues to clear and retry once
if grep -qi "could not be sent\|email.*unavailable\|Google Workspace MCP.*unresponsive\|email.*blocked" "${LOG_FILE}" 2>/dev/null; then
  echo "" >> "${LOG_FILE}"
  echo "=== RETRY: Email send failure detected. Waiting 60s then retrying... ===" >> "${LOG_FILE}"
  sleep 60

  RETRY_PROMPT="My morning brief partially failed — Google Workspace MCP was down. Please compile and send a fresh ${MODE} briefing now. Send the HTML email and Slack summary."
  "${CLAUDE_BIN}" \
    --print \
    --dangerously-skip-permissions \
    --model sonnet \
    "${RETRY_PROMPT}" \
    >> "${LOG_FILE}" 2>&1 || true

  echo "=== RETRY completed: $(date) ===" >> "${LOG_FILE}"
fi

# Determine final exit code based on email delivery
# Exit 1 if email was never successfully sent (grep for success signals)
FINAL_EXIT=0
if grep -qi "could not be sent\|email.*unavailable\|email.*blocked" "${LOG_FILE}" 2>/dev/null; then
  # Check if a later successful send overrode the failure
  if ! grep -qi "email sent\|message sent successfully\|Full HTML briefing sent" "${LOG_FILE}" 2>/dev/null; then
    echo "ERROR: Email was never successfully sent (even after retry)." >> "${LOG_FILE}"
    FINAL_EXIT=1
  fi
fi

echo "=== Briefing run completed: $(date) (exit code: ${FINAL_EXIT}) ===" >> "${LOG_FILE}"

# Keep only last 30 days of logs
find "${LOG_DIR}" -name "briefing-*.log" -mtime +30 -delete 2>/dev/null || true

exit ${FINAL_EXIT}
