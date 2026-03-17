# /slack-search — Search Slack

Search Slack messages and channels for relevant conversations.

## Instructions

1. Ask what they're looking for if not provided as an argument.
2. Use `mcp__slack__slack_search_public_and_private` to search messages.
3. Summarize results — highlight the most relevant messages with:
   - Who said it, which channel, when, brief quote or summary
4. If results are too broad, offer to narrow by channel or date.
5. If the user wants to read a full thread, use `mcp__slack__slack_read_channel` with the channel ID.
6. Key channels to know:
   - #pathfinder-support (C067SSZ1AMT) — escalations
   - #phils-gumloop-agent (C0AC2NK50QN) — test channel

## Example usage

```
/slack-search merchant volume drop
/slack-search #pathfinder-support kiosk issue
/slack-search Q1 launch timeline
/slack-search from:mallory onboarding
```
