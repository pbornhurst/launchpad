# /daily-brief — Morning Briefing

Get a consolidated morning briefing: volume alerts, card metrics, calendar, email, support, onboarding, pattern alerts, and action items. Delivered as a styled HTML email + condensed Slack summary.

## Instructions

Dispatch the `briefing-compiler` agent to compile a daily briefing. The agent runs 4 parallel sub-agents for speed:
- **Volume + Card Metrics** (Sheets + Snowflake)
- **Calendar + Email** (Google Workspace)
- **Slack + Intercom + Onboarding** (#pathfinder-support, Intercom, #pathfinder-mxonboarding)
- **Pattern Alerts** (Support Intelligence Tracker)

Results are assembled into a styled HTML email sent to Phil + a condensed summary posted to #phils-gumloop-agent.

If the user says "in the background", dispatch the agent in the background.

Pass any additional context from the user's message through to the agent (e.g., extra channels, specific focus areas).

## Example usage

```
/daily-brief
/daily-brief in the background
```
