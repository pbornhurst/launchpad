# /gdrive-search — Search Google Drive

Find documents, spreadsheets, and presentations in Google Drive.

## Instructions

1. Ask what they're looking for if not provided as an argument.
2. Use `mcp__claude_ai_Google_Drive__search_files` with:
   - `query`: the search terms
   - Or use `mcp__claude_ai_Google_Drive__list_recent_files` for recently-modified items
3. Present results as a clean list:
   - Document title, type (Doc, Sheet, Slides, PDF), last modified, owner
4. If the user wants to read a document, use `mcp__claude_ai_Google_Drive__read_file_content`.
5. Summarize content rather than dumping raw text.

## Example usage

```
/gdrive-search Q1 OKR planning
/gdrive-search merchant onboarding template
/gdrive-search pathfinder roadmap
```
