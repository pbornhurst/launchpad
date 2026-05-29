#!/bin/bash
# Weekly DoorDash in-store help center refresh.
# Re-scrapes Zendesk Help Center → data/help-center-map.{json,md}.
# Designed for launchd (Mondays at 7am PST), but safe to run manually.

set -euo pipefail

WORKSPACE="/Users/philip.bornhurst/Claude/launchpad"
LOG_DIR="${WORKSPACE}/logs"
TS="$(date +"%Y-%m-%dT%H:%M:%S%z")"
LOG_FILE="${LOG_DIR}/help-center-refresh.log"

mkdir -p "${LOG_DIR}"

cd "${WORKSPACE}"

{
  echo "===== help-center refresh started ${TS} ====="
  if [ ! -f .env ]; then
    echo "ERROR: .env not found at ${WORKSPACE}/.env"
    exit 1
  fi
  /usr/bin/env python3 scripts/scrape_zendesk_help_center.py
  echo "===== refresh complete $(date +"%Y-%m-%dT%H:%M:%S%z") ====="
  echo
} >> "${LOG_FILE}" 2>&1
