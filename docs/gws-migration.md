# Google Workspace Access — gws CLI Migration

> **The `google-workspace` MCP (`mcp__google-workspace__*`) is DEAD.** Its OAuth client
> (`730260651999-…`) is blocked by DoorDash admin policy (`admin_policy_enforced`) and will
> not re-auth. Do NOT call any `mcp__google-workspace__*` tool. Use the mappings below.

Verified working 2026-06-05. Auth: `gws` CLI authed via Phil's own GCP project
`phil-workspace-mcp` (client `22269490876-…`). See memory `gws-cli-auth`.

## Routing rules

- **Sheets** → `gws` CLI (no MCP equivalent for ranged read/write).
- **Docs** → `gws` CLI (read + HTML-import + batchUpdate) or the `productivity:editing-google-docs` skill.
- **Gmail / Calendar / Drive** → claude.ai MCPs (`mcp__claude_ai_Gmail__*`, `mcp__claude_ai_Google_Calendar__*`, `mcp__claude_ai_Google_Drive__*`) — separate DoorDash-trusted OAuth path, all working. `gws gmail|calendar|drive` also works as a fallback.
- **Drop the `user_google_email` param entirely** — neither gws nor the claude.ai MCPs need it.
- gws prints clean JSON to stdout; a `Using keyring backend: keyring` line goes to **stderr** and can leak into pipes — strip it before `json.load` (e.g. `gws … 2>/dev/null | python3 …`).

## SHEETS → `gws sheets`

| Old `mcp__google-workspace__` | New |
| --- | --- |
| `read_sheet_values(id, range)` | `gws sheets +read --spreadsheet ID --range "Tab!A1:F50"` |
| `modify_sheet_values(id, range, values)` | `gws sheets spreadsheets values update --params '{"spreadsheetId":"ID","range":"Tab!A1","valueInputOption":"USER_ENTERED"}' --json '{"values":[[...]]}'` |
| `append_table_rows` / append | `gws sheets +append --spreadsheet ID --range "Tab" --values '[["a","b"]]'` (or `spreadsheets values append`) |
| `get_spreadsheet_info` / `list_sheet_tables` | `gws sheets spreadsheets get --params '{"spreadsheetId":"ID"}'` |

**Master Hub win:** gws has NO 50-row display cap. One `gws sheets +read --range "B1:E800"` replaces the old 16-parallel-chunk pattern. (Memory `feedback_master_hub_read_pattern` is obsolete for gws.)

## DOCS → `gws docs` (+ `productivity:editing-google-docs`)

| Old | New |
| --- | --- |
| `get_doc_content` / `get_doc_as_markdown` | `gws docs documents get --params '{"documentId":"ID","includeTabsContent":true}'` |
| `import_to_google_doc` (HTML) — **the key one** | Upload HTML to Drive with conversion: `gws drive files create --json '{"name":"Title","mimeType":"application/vnd.google-apps.document"}' --upload file.html --upload-content-type "text/html"` → returns `{"id":...}`. **Verified: preserves headings + tables.** Put the doc in a folder via `parents` in the JSON, or move after. |
| `create_doc` (plain) | `gws docs documents create --json '{"title":"..."}'` |
| `batch_update_doc` / `insert_doc_elements` / `create_table_with_data` | `gws docs documents batchUpdate --params '{"documentId":"ID"}' --json '{"requests":[...]}'`, OR invoke skill `productivity:editing-google-docs` (handles index math). |
| `inspect_doc_structure` / `debug_table_structure` | `gws docs documents get` then inspect the `body.content` array. |
| `export_doc_to_pdf` | `gws drive files export --params '{"fileId":"ID","mimeType":"application/pdf"}' -o out.pdf` |

**HTML-import is the preferred path for generated docs** (churn-risk, qbr, benchmark, weekly-mindmap, mx deep dives): build the styled HTML exactly as before per the CLAUDE.md "Google Docs Formatting" rules, then convert via the `gws drive files create` one-liner above. Set the destination folder with `"parents":["FOLDER_ID"]` in the `--json` metadata.

### Docs `batchUpdate` gotchas — VERIFIED on gws 2026-06-05 (use these, the older meeting-capture formulas were wrong)

For hand-built table prepends via `gws docs documents batchUpdate` (the meeting-capture path), the index math differs from the dead MCP. Empirically measured:

- **Empty-table span:** `span = 2 + R + 2*R*C` (NOT `3 + R + 2*R*C` — off by one).
- **Cell text-insert index:** insert at the cell's **inner paragraph** start, which is `tableCell.startIndex + 1`. Get it from the structure as `cell["content"][0]["startIndex"]`. Inserting at the raw `tableCell.startIndex` fails with `"insertion index must be inside the bounds of an existing paragraph"`. Always re-read the doc (`documents get`) after inserting empty tables and use the actual inner-paragraph indices — do not trust a computed cell formula.
- **Inherited paragraph style (the silent one):** text inserted at index 1 **inherits the namedStyleType of whatever paragraph currently starts the doc**. Prepending into a doc whose top line is a previous `HEADING_1` makes ALL your new body/bullet paragraphs Heading 1. You MUST explicitly set `namedStyleType: "NORMAL_TEXT"` (via `updateParagraphStyle`) on every non-heading paragraph you insert; setting only the headings is not enough.
- **`insertTable` injects an implicit paragraph** before the table, so forward-cursor math through interleaved text+tables drifts. Robust pattern: insert the full text with placeholder lines, then replace placeholders with tables bottom-up, then re-read for cell indices (see [[feedback_docs_prepend_placeholder_pattern]]).

### Sheets append gotcha — tab-targeted writes

- `gws sheets +append` has **no `--range`/tab flag** — it appends to the first sheet only. Do NOT use it for a specific tab.
- `gws sheets spreadsheets values append` with a **bare tab range** (`"range":"v2"`) lets Google's table-detection pick the wrong region — observed appending into columns V:Z and `INSERT_ROWS` shifted live data down by a row. **Avoid append for tab-scoped writes.**
- **Correct, deterministic pattern:** read the tab's column A to count rows, then `gws sheets spreadsheets values update` to an explicit `"<Tab>!A{n+1}:E{n+1}"` range. No table-detection, no row shifts.

## GMAIL → `mcp__claude_ai_Gmail__*` (preferred) or `gws gmail`

| Old | New (claude.ai MCP) |
| --- | --- |
| `search_gmail_messages` | `mcp__claude_ai_Gmail__search_threads` or `search` |
| `get_gmail_message_content` / `_batch` / `get_gmail_thread_content` | `mcp__claude_ai_Gmail__get_thread` |
| `draft_gmail_message` | `mcp__claude_ai_Gmail__create_draft` |
| `send_gmail_message` | `mcp__claude_ai_Gmail__create_draft` then confirm + send, or skill `productivity:send-gmail-message`, or `gws gmail messages send` |
| `list_gmail_labels` | `mcp__claude_ai_Gmail__list_labels` |
| `label_message` / `modify_gmail_message_labels` | `mcp__claude_ai_Gmail__label_thread` / `label_message` |

Gmail label IDs (e.g. `Launcher Reports`) are discoverable via `list_labels`. **Confirm-before-send still applies** (CLAUDE.md rule 10) — draft first.

## CALENDAR → `mcp__claude_ai_Google_Calendar__*`

| Old | New |
| --- | --- |
| `get_events` / `list_events` | `mcp__claude_ai_Google_Calendar__list_events` |
| `list_calendars` | `mcp__claude_ai_Google_Calendar__list_calendars` |
| `create_event` / `manage_event` | `mcp__claude_ai_Google_Calendar__create_event` / `update_event` / `delete_event` |
| `get_event` | `mcp__claude_ai_Google_Calendar__get_event` |

## DRIVE → `mcp__claude_ai_Google_Drive__*` (read) / `gws drive` (write)

| Old | New |
| --- | --- |
| `search_drive_files` / `search_docs` | `mcp__claude_ai_Google_Drive__search_files` |
| `list_docs_in_folder` / `list_drive_items` | `mcp__claude_ai_Google_Drive__search_files` with a `'parents' in '<FOLDER_ID>'` query, or `list_recent_files` |
| `get_drive_file_content` / `read_file_content` | `mcp__claude_ai_Google_Drive__read_file_content` |
| `create_drive_folder` | `gws drive files create --json '{"name":"...","mimeType":"application/vnd.google-apps.folder","parents":["PARENT_ID"]}'` |
| `create_drive_file` / `copy_drive_file` | `gws drive files create` / `gws drive files copy` |
| `set_drive_file_permissions` / `manage_drive_access` | `gws drive permissions create --params '{"fileId":"ID"}' --json '{"role":"writer","type":"domain","domain":"doordash.com"}'` |
| `get_drive_shareable_link` | use the `webViewLink` field from `gws drive files get --params '{"fileId":"ID","fields":"webViewLink"}'` |

## Quick reference — auth / health

```bash
gws auth status                 # check token
gws auth login -s docs,sheets,drive,gmail,calendar   # re-auth (prints URL; open manually)
gws sheets +read --spreadsheet 1uS_noBD2nTYjpM6VJvIQwSLMKA_tLkiyo-3dHwi0Ta8 --range "Log!A1:A1"  # smoke test
```
