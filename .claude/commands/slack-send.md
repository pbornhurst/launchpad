# /slack-send — Send a Slack Message

Compose and send a message to a Slack channel or user.

## Instructions

1. Ask for destination (channel or user) and message content if not provided.
2. Draft the message and show it to the user for review.
3. **ALWAYS confirm before sending.** Never send without explicit user approval.
4. Use `mcp__slack__slack_post_message` to post the message.
5. Confirm delivery with channel and timestamp.
6. Default posting channel for briefings: #phils-gumloop-agent (C0AC2NK50QN)

## Tone guidance

- Match requested tone (casual, formal, etc.)
- Default to professional but friendly
- Keep messages concise and action-oriented (Phil's style)

## Example usage

```
/slack-send Tell #pathfinder-support the kiosk fix is deployed
/slack-send Post today's brief to #phils-gumloop-agent
/slack-send DM @mallory about the QBR schedule
```
