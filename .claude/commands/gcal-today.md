# /gcal-today — Today's Calendar

Show today's schedule and upcoming meetings.

## Instructions

1. Use `mcp__google-workspace__get_events` with:
   - `user_google_email: "philip.bornhurst@doordash.com"`
   - `time_min`: today's start in RFC3339 (e.g., "2026-03-16T00:00:00-07:00")
   - `time_max`: today's end in RFC3339
2. Present as a clean timeline in PST:
   - Time, meeting title, duration
   - Attendees (abbreviated if many)
   - Video link if present
3. Highlight:
   - Next upcoming meeting and time until it starts
   - Any gaps / free blocks
   - Any conflicts or double-bookings
   - Any mx calls (flag for call-prep)
4. If asked, look ahead to tomorrow or rest of week.

## Example usage

```
/gcal-today
/gcal-today what's my afternoon look like
/gcal-today tomorrow
```
