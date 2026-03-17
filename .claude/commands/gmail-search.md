# /gmail-search — Search Gmail

Search Gmail for emails matching a query.

## Instructions

1. Ask what they're looking for if not provided as an argument.
2. Use `mcp__google-workspace__search_gmail_messages` with:
   - `user_google_email: "philip.bornhurst@doordash.com"`
   - `query`: the search terms (supports Gmail search operators like `from:`, `to:`, `is:unread`, `after:`, `before:`, `subject:`)
3. Present results as a summary list:
   - From / To, Subject, Date, brief preview
4. If the user wants to read a full email, use `mcp__google-workspace__get_gmail_message_content`.
5. For threads, use `mcp__google-workspace__get_gmail_thread_content`.
6. **Never send or reply to emails** unless the user explicitly asks and confirms.

## Example usage

```
/gmail-search invoices from last week
/gmail-search from:mallory pathfinder
/gmail-search is:unread from:sales
/gmail-search subject:QBR after:2026/03/01
```
