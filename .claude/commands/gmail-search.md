# /gmail-search — Search Gmail

Search Gmail for emails matching a query.

## Instructions

1. Ask what they're looking for if not provided as an argument.
2. Use `mcp__claude_ai_Gmail__search_threads` (or `search`) with:
   - `query`: the search terms (supports Gmail search operators like `from:`, `to:`, `is:unread`, `after:`, `before:`, `subject:`)
3. Present results as a summary list:
   - From / To, Subject, Date, brief preview
4. If the user wants to read a full email or thread, use `mcp__claude_ai_Gmail__get_thread`.
5. To list available labels, use `mcp__claude_ai_Gmail__list_labels`.
6. **Never send or reply to emails** unless the user explicitly asks and confirms.

## Example usage

```
/gmail-search invoices from last week
/gmail-search from:mallory pathfinder
/gmail-search is:unread from:sales
/gmail-search subject:QBR after:2026/03/01
```
