# /calendly-prep — Calendly Call Preparation

Scan today's calendar for Calendly-scheduled meetings and prepare for each one: match to Master Hub, create account management folder and running notes doc, run internet research, and send Slack summary.

## Instructions

Dispatch the `calendly-call-prep` agent to scan today's calendar and prepare for all Calendly meetings.

The agent will:
1. Scan today's calendar for events with "Event Name: 15 Minute Meeting" in the description
2. Match each event to the Master Hub using fuzzy matching on name, email, phone, and address
3. Find or create an account management folder under the Account Management parent folder
4. Create a formatted Running Notes Google Doc in the mx folder
5. Run internet research on the restaurant (website, reviews, press, social media, talking points)
6. Send a Slack notification to #phils-gumloop-agent with all links and the full research brief

If the user says "in the background", dispatch the agent with `run_in_background: true`.

## Example usage

```
/calendly-prep
/calendly-prep in the background
"Prep my Calendly calls"
"Do I have any Calendly meetings today?"
```
