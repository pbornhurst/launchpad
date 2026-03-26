# /weekly-recap — Weekly Summary

Generate a comprehensive weekly summary across all tools and data sources. Uses the same briefing-compiler agent in weekly mode — expanded time windows, extra Slack channels, product feedback, and weekly-specific sections.

## Instructions

Dispatch the `briefing-compiler` agent in **weekly mode**. Tell the agent: "Compile a weekly briefing."

The agent expands to include:
- 7-day time windows (instead of 24h)
- #pathfinder-sales-team for CW submissions
- #pathfinder-onboarding-team for install/launch updates
- Product Feedback Tracker for new entries
- Weekly-only sections: By the Numbers, Sales Pipeline, Onboarding Activity, Wins, Open Items, Next Week Preview

Results are delivered as a styled HTML email + Slack summary, same as the daily brief.

If the user says "in the background", dispatch the agent in the background.

## Example usage

```
/weekly-recap
/weekly-recap in the background
/weekly-recap last 2 weeks
/weekly-recap Mallory's accounts only
```
