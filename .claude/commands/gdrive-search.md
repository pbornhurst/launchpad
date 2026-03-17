# /gdrive-search — Search Google Drive

Find documents, spreadsheets, and presentations in Google Drive.

## Instructions

1. Ask what they're looking for if not provided as an argument.
2. Use `mcp__google-workspace__search_drive_files` with:
   - `user_google_email: "philip.bornhurst@doordash.com"`
   - `query`: the search terms
3. Present results as a clean list:
   - Document title, type (Doc, Sheet, Slides, PDF), last modified, owner
4. If the user wants to read a document:
   - For Docs: use `mcp__google-workspace__get_doc_as_markdown`
   - For Sheets: use `mcp__google-workspace__read_sheet_values`
   - For other files: use `mcp__google-workspace__get_drive_file_content`
5. Summarize content rather than dumping raw text.

## Example usage

```
/gdrive-search Q1 OKR planning
/gdrive-search merchant onboarding template
/gdrive-search pathfinder roadmap
```
