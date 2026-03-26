#!/bin/bash
# Mx Alert Monitor — Proactive Anomaly Detection
# Checks for gone-dark stores and severe volume drops.
# Posts to Slack ONLY when anomalies are found.
# Designed for macOS launchd scheduling (3x daily: 10:30am, 2:30pm, 5:30pm PST).
#
# Usage:
#   ./scripts/mx-alert-monitor.sh
#
# Prerequisites:
#   - claude CLI installed at /usr/local/bin/claude
#   - MCP servers configured in the launchpad workspace
#   - OAuth tokens valid for Google Workspace, Slack

set -euo pipefail

# Configuration
WORKSPACE="/Users/philip.bornhurst/Claude/launchpad"
LOG_DIR="${WORKSPACE}/logs"
CLAUDE_BIN="/usr/local/bin/claude"
DATE=$(date +"%Y-%m-%d")
TIME=$(date +"%H%M")

# Ensure log directory exists
mkdir -p "${LOG_DIR}"

# Log file for this run
LOG_FILE="${LOG_DIR}/monitor-${DATE}-${TIME}.log"

echo "=== Mx Alert Monitor started: $(date) ===" >> "${LOG_FILE}"

# Wait for Tailscale VPN connectivity (shorter timeout — this runs more frequently)
MAX_WAIT=120
INTERVAL=10
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

PROMPT="Run /mx-alert-monitor. This is a headless automated check — post to Slack only if anomalies found, otherwise just log and exit."

# Run Claude in headless mode
cd "${WORKSPACE}"
"${CLAUDE_BIN}" \
  --print \
  --dangerously-skip-permissions \
  --model sonnet \
  "${PROMPT}" \
  >> "${LOG_FILE}" 2>&1

EXIT_CODE=$?

echo "=== Mx Alert Monitor completed: $(date) (exit code: ${EXIT_CODE}) ===" >> "${LOG_FILE}"

# Keep only last 7 days of monitor logs
find "${LOG_DIR}" -name "monitor-*.log" -mtime +7 -delete 2>/dev/null || true

exit ${EXIT_CODE}
