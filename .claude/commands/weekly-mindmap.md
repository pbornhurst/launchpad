# /weekly-mindmap — Weekly Cross-AM Mind Map

Generate a structured cross-AM mind map for the week: themes clustered across calls, active churn risks, wins, product feedback roll-up, stakeholder graph, by-AM summary, and action items. Output is a formatted Google Doc in the `Weekly Mind Maps 2026` folder.

> This command surfaces signal that's invisible at the per-call level: "4 mx hit the same bug this week" instead of 4 isolated bullets across 4 docs.

## Instructions

Dispatch the `weekly-mindmap` agent. It will:
- Parse the window from the user's input (default: last completed Mon-Sun)
- Pull all Phil + Mallory calls from the input tracker for that window
- Split the call roster and dispatch N parallel extraction sub-agents
- Synthesize cross-AM patterns, risk clusters, wins, feedback, and stakeholder graph
- Write a formatted Google Doc (H1/H2/H3, real bullets, Arial 11) to `Weekly Mind Maps 2026`
- Return the link + a short top-line summary

If the user says "in the background", dispatch the agent with `run_in_background: true`.

Pass any additional context through (specific AMs, custom date range, narrower focus).

## Examples

```
/weekly-mindmap                          ← default: last completed week
/weekly-mindmap week of 4/13             ← explicit week start
/weekly-mindmap 2026-04-01 to 2026-04-19 ← custom range
/weekly-mindmap in the background        ← async
```

## Notes

- Output folder: `Weekly Mind Maps 2026` (in `2026/`)
- Requires the input tracker (`1OMJ-3KK_ge_aLy_kJZR-2AbehZdKeviOpmHOILmS8lM`) to be up-to-date
- Complements `/weekly-recap` (narrative) — this one is structured pattern synthesis
