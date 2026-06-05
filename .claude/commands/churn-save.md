# /churn-save — Churn Save Celebration Template

Generate a structured "churn save" writeup from one or more input sources (running notes doc, Slack thread, emails, call transcript, etc.). Designed to make AM saves visible to xfn partners who otherwise only see the churns.

The eventual home for this is a Slack workflow — so the output is intentionally Slack-mrkdwn formatted and field-by-field.

## Instructions

1. **Collect input sources** from the user. Any combination of:
   - Running Notes doc URL (preferred — has structured PRISM-TnA notes)
   - Slack channel ID + date range, or specific thread URL
   - Gmail thread IDs or search query
   - Granola meeting ID / transcript
   - Free-text context Phil types directly

2. **Read every source in parallel.** Use the relevant tool for each:
   - Bash: `gws docs documents get --params '{"documentId":"ID","includeTabsContent":true}'` for docs
   - `mcp__slack__slack_read_channel` or `slack_read_thread` for Slack
   - `mcp__claude_ai_Gmail__get_thread` for email
   - `mcp__granola__get_meeting_transcript` for Granola

3. **Segment the content into these 7 fields.** Be selective — premise is one or two sentences, not a recap. The save is the story, not the threat.

   | Field | What goes here |
   |---|---|
   | **mx** | Business name + Store ID |
   | **AM** | Who led the save |
   | **Premise** | What was the churn risk? One or two sentences — trigger + what was at stake. |
   | **Tactics** | What you (and the team) actually did. Bullet the moves. |
   | **Result** | Where the mx stands now — tone, signals, concrete wins. |
   | **Next steps** | What's still open to lock this in. |
   | **Honorable mentions** | xfn partners, launchers, support, product — name names with the specific contribution. |

4. **Format the output for Slack mrkdwn** (asterisks for bold, `•` bullets, emoji shortcodes like `:trophy:`, no markdown tables). Use this structure:

   ```
   :tada: *Churn Save — [mx Name]*

   *AM:* [name]

   *Premise:* [1-2 sentences]

   *Tactics:*
   • [move 1]
   • [move 2]
   • [move 3]

   *Result:* [where mx stands now]

   *Next steps:*
   • [open item 1]
   • [open item 2]

   *Honorable mentions:* :trophy: [Name] ([Team]) — [specific contribution]. [Name] — [contribution].
   ```

5. **Show the draft to Phil and confirm** before doing anything else. Default action is "show only" — Phil will tell you whether to:
   - Slack DM it to himself (`channel_id: U07NNV8QX60`)
   - Post to a specific channel (e.g., #pathfinder-pulse)
   - Just return it as text

6. **Never auto-post.** Per Rule 10, explicit approval required before sending Slack.

## Writing guidelines

- **Premise is tight.** One or two sentences. If the premise is longer than the result, you're writing a churn post-mortem, not a save celebration.
- **Tactics are concrete moves, not adjectives.** "Same-day on-site visit fixed saved-order deletes" beats "team rallied quickly."
- **Result names the flip.** Before → after. Quote the mx if there's a great line ("chomping at the bit," "main reason he didn't churn was Crystal").
- **Honorable mentions are specific.** Not "thanks to the launch team" — name the person and what they did. This is the whole point of the exercise.
- **Avoid the word "we" in tactics.** Use names. xfn visibility is the goal.

## Example usage

```
/churn-save https://docs.google.com/document/d/14mNds8P3c5mecx-Qoeoc1mUVKMAuU6-wVYH1Uk4-BYw/edit and slack channel C0B3STD3JKE from 5/13-5/14
/churn-save Running notes for Pizza Palace + the email thread with Corey from last week
/churn-save
```

If invoked with no args, ask Phil for the mx and at least one input source.
