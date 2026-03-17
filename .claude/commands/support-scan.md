# /support-scan — Support Channel Scanner

Scan #pathfinder-support for recent escalations and issues.

## Instructions

1. Read recent messages from #pathfinder-support using `mcp__slack__slack_read_channel`:
   - Channel ID: C067SSZ1AMT
   - Default: last 24 hours. User can specify a different window.
2. Categorize messages:
   - **Escalations** — Messages tagged urgent, mentioning Phil/Mallory, or requesting AM help
   - **New Issues** — Bug reports, outage reports, mx complaints
   - **Resolved** — Issues marked resolved or with resolution messages
   - **Informational** — General updates, announcements
3. For each escalation, try to identify the merchant:
   - Search for Store ID or mx name in the message
   - Cross-reference with Master Hub if found
4. Present as:

```
## Support Scan: #pathfinder-support
**Period:** Last 24 hours | **Total messages:** N

### Escalations Needing Response (N)
- **[mx name / Store ID]** — Issue summary (posted by @user, X hours ago)

### New Issues (N)
- Issue summary (posted by @user, X hours ago)

### Recently Resolved (N)
- Issue summary — resolved by @user

### Summary
- X open escalations, Y new issues, Z resolved
- Highest priority: [describe]
```

## Example usage

```
/support-scan
/support-scan last 3 days
/support-scan mentioning kiosk
```
