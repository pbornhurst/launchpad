# /email-triage — Email Triage & Draft

Scan my Gmail inbox for unanswered mx inbounds, identify each mx, pull supporting context (Master Hub + Running Notes + L7D volume + relationship history + Intercom), then save a draft reply in my voice on each thread. Drafts only — nothing ever sends. Mirrors the Co-Work `email-monitoring` skill but runs locally on demand.

Backs into a self-improving voice profile: every draft is logged to a Google Doc, and on each subsequent run the agent reconciles drafts against what I actually sent and learns the delta.

## Usage

```
/email-triage                    # default: emails received since last /email-triage run (or last 24h on first run)
/email-triage --since 2h         # only process inbounds from the last 2 hours
/email-triage --since 7d         # last 7 days
/email-triage --all              # process every unanswered inbound currently in inbox, no time bound
/email-triage in the background  # dispatch the agent with run_in_background: true
```

## Instructions

1. Parse `$ARGUMENTS` for a `--since <Nh|Nd>` window or `--all`. If none, default to the timestamp in `~/Claude/launchpad/.email-triage/last-run.txt` (or 24h ago if the file doesn't exist).
2. Dispatch the `email-triage` agent with the resolved window and the `--all` flag passthrough.
3. The agent handles Phase 3 reconciliation, voice calibration, per-email parallel processing, Gmail draft creation, Voice Learning Log writes, and the in-chat summary.
4. After the agent reports completion, write the run completion timestamp to `~/Claude/launchpad/.email-triage/last-run.txt` (ISO 8601, America/Los_Angeles). The agent prints this value at the end of its run.
5. If the user added "in the background", dispatch with `run_in_background: true` and let them know they'll be notified when it finishes.

## Reference

The full behavioral spec — eligibility rules, mx identification order, context pull, draft format, voice rules, Voice Learning Log structure — lives in the [email-monitoring skill doc](https://docs.google.com/document/d/1_K2nmV0MDFfCrdQ2x4fBOAdA-ugoH-i0X9zwJaTWMJc/edit). The `email-triage` agent in this project is the local implementation of that spec. Keep them in sync if you edit one — the doc is the source of truth.
