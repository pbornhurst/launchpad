---
name: meeting-capture
description: Scan recent Granola meetings for mx calls, generate structured PRISM-TnA notes from the transcript, prepend them to the mx's Running Notes doc, and log the call to the Running Notes Input Tracker. Trigger on "run meeting capture", "capture my meetings", "process my recent mx calls", "capture granola meetings", "prepend meeting notes to running notes", "log my recent calls", or /meeting-capture. Scans and classifies every candidate first, then confirms the process list with Phil before writing anything.
---

# meeting-capture — Capture Granola mx Calls to Running Notes

Scan recent Granola meetings for mx calls, generate structured PRISM-TnA notes from the transcript, prepend them to the mx's Running Notes doc, and log the call to the Running Notes Input Tracker.

**Confirms before writing.** Lists last 7d of Granola meetings in one call, batch-fetches all candidate notes upfront, then walks tier windows (2h → 12h → 24h → 48h → 7d) IN MEMORY with stop-the-world early-exit on the first tracker-duplicate hit. Classifies every candidate (processable vs. skipped) and waits for Phil's explicit go-ahead before touching any doc or tracker.

## Instructions

### 1. Discover candidates (one list call, one batched fetch, in-memory tier walk)

**Design:** the front-end discovery does at most **3 API calls**: one `list_meetings`, one `gws sheets +read` for the tracker dedupe set, and one or two `get_meetings` batches. The tier walk is purely in-memory over the already-fetched data — its job is the stop-the-world early-exit, not gating I/O.

**Parallelization:** Step 3's reads (Master Hub header + body + tracker dedupe) are independent of Step 1c's `get_meetings` batch. Fire them in the same message as parallel tool calls — the tier walk in 1d needs both sets of data, but neither needs the other to start. This is the difference between a serial 4-call chain and a 2-round-trip discovery phase.

**1a. List meetings — 7-day custom window.** Call `mcp__granola__list_meetings` with:
- `time_range: "custom"`
- `custom_start: <today minus 7 days, ISO format YYYY-MM-DD>`
- `custom_end: <today, ISO format YYYY-MM-DD>`

Why custom over `last_30_days`: a 30-day window returns ~130+ meeting summaries (~70KB) that overflow the tool-result token limit, forcing a file-spillover round trip via Bash. A 7-day window returns ~25 meetings inline, no spillover.

**1b. Parse, tier-bucket, and emit IDs in one Python invocation.** Pipe the `list_meetings` text through a single `python3 <<PY ... PY` Bash call that:

1. Regex-extracts each `<meeting id="..." title="..." date="...">` triplet.
2. Parses the date string (`%b %d, %Y %I:%M %p` after stripping the trailing `PDT`/`PST`) and computes `hours_ago = (datetime.now() - parsed_dt).total_seconds() / 3600`. (Granola timestamps render in the event creator's timezone — usually PT for Phil's calendar, but cross-reference Google Calendar via `mcp__claude_ai_Google_Calendar__list_events` if a specific meeting's date looks off.)
3. Sorts newest-first.
4. Buckets each meeting into Tier 1-5 by `hours_ago`:
   - Tier 1: 0-2h
   - Tier 2: 2-12h
   - Tier 3: 12-24h
   - Tier 4: 24-48h
   - Tier 5: 48-168h
5. Prints a single JSON blob with: meeting list (id, title, date_str, hours_ago, tier), tier-bucket sizes, and a deduped list of all candidate IDs to fetch (Tier 1 ∪ Tier 2 ∪ Tier 3 ∪ Tier 4 ∪ Tier 5, capped at 10 per `get_meetings` call).

This replaces what was previously two Bash steps with one.

**1c. Batched note fetch (single round trip when possible).** From step 1b's deduped ID list, call `mcp__granola__get_meetings` with up to 10 IDs per call. For typical 7-day windows the candidate count is ≤10 and this is one round trip; if >10, fire as many parallel `get_meetings` calls as needed (each capped at 10 IDs) in a single message. Pre-filter on a denylist of obvious recurring internal meetings before fetching, so we don't waste IDs on team standups: skip titles matching (case-insensitive) any of `^AM Team Super Standup`, `^Pathfinder (Brief|Ops|Prod)`, `^Phil / `, `^Philip / `, `Weekly 1:1$`, `^Strategic Initiatives Check-In`, `^DD <> CE Weekly`, `^VOTM Sync`, `^Monthly Newsletter Jam`. (When in doubt, fetch — the cost of one extra `get_meetings` slot is small, and missing an mx call is worse than fetching one internal meeting.)

**1d. Tier walk in memory (stop-the-world).** With every candidate's notes now resident, walk Tier 1 → Tier 5 in newest-first order. For each meeting in each tier:
- Run marker detection (Step 2) on the private notes.
- If marker matches and `(store_id, meeting_date)` is in the tracker dedupe set: **halt** all further tier expansion. Everything older in this run is presumed already processed. Record this as the stop point for the confirmation summary.
- If marker matches and not in dedupe set: append as `processable` (or appropriate `skipped-*` bucket — see Step 4) to the candidate list.
- If no marker: skip silently, do NOT count toward stop trigger.

The walk is pure local CPU; no API calls. The stop-the-world benefit is preserved — it just operates on the already-fetched data.

**1e. How the dedupe signal works.** Load the tracker v2 dedupe set ONCE (Section 3) before the tier walk. Every successfully captured meeting in the current run also gets added to the in-memory dedupe set so it short-circuits later in the same walk. The tracker is append-only, so a `(store_id, date)` pair found there means that exact mx call was already captured — nothing older could plausibly be new.

**1f. Edge cases:**
- Non-`mx call` meetings (no marker) do NOT count toward the stop trigger. Skip them silently.
- `mx call` meetings that are missing a Store ID, not in Master Hub, or have no Running Notes doc count as `skipped-*` but DO NOT trigger stop — they weren't captured, so we have no signal that older meetings were either.
- Tier 5 completes with zero captures and zero stop hits → the summary notes "no new mx calls in last 7 days" — true base case for re-runs.
- If 7 days isn't enough (Phil names a meeting older than 7d in step 4 modify), widen `custom_start` to 14d and re-run steps 1a-1d. Don't widen by default — the savings come from the narrow window.

### 2. Identify mx calls

On each meeting's private notes, scan the **first 8 non-empty lines** for an identifier matching any of these (case-insensitive):

- `mx call`
- `#mx-call`
- `mx-call`
- `MX CALL`

Regex (case-insensitive, multiline): `^\s*#?\s*mx[\s-]call\b`

If no match, drop the meeting. If matched, continue parsing:

- **Store ID** (required): scan the next 3 non-empty lines after the identifier for a numeric token matching `\b\d{4,10}\b`. Capture the first hit. If absent, mark this meeting `skipped-no-store-id` and continue to the next meeting.
- **Merchant contact** (optional): the next non-empty line after the Store ID that is NOT another numeric token. If absent, fall back later to non-`@doordash.com` attendees from the meeting metadata.

### 3. Pre-load shared data (one-shot reads)

Do these once per command run, before any per-meeting work:

**Master Hub.** Use `1ndVs2lPhS5frpkEV0KzK7ec5aS18fmr9h1BQEu099E4` — the IMPORTRANGE view with a single header row (cleaner to read than the source sheet). Default first tab (`gid=0`). Column headers live on **row 1**. Data starts on row 2.

**Master Hub header confirmation** (future-proof against column shifts):

- `gws sheets +read --spreadsheet 1ndVs2lPhS5frpkEV0KzK7ec5aS18fmr9h1BQEu099E4 --range "A1:CA1"`
- Locate the column index where header equals exactly `"Running Notes"`. Expected: column BV (index 73). If it has moved, use the discovered column.

**Master Hub body.** gws has no 50-row display cap, so a single ranged read returns the full sheet:

- `gws sheets +read --spreadsheet 1ndVs2lPhS5frpkEV0KzK7ec5aS18fmr9h1BQEu099E4 --range "A1:CA800"` (widen the row bound if the book grows past 800 rows). Headers on row 1, data from row 2.
- Build an in-memory dict keyed by Store ID (column E, index 4), capturing:
  - Business Name (column B, index 1)
  - Store ID (column E, index 4)
  - Mx Tier (column F, index 5)
  - Account Manager (column I, index 8)
  - DM Name (column U, index 20)
  - DM Email (column V, index 21)
  - Running Notes URL (column BV, index 73, or whatever the discovered Running Notes column is)

Normalize Store IDs to strings (strip whitespace) when indexing.

**Tracker dedupe set:**

- `gws sheets +read --spreadsheet 1OMJ-3KK_ge_aLy_kJZR-2AbehZdKeviOpmHOILmS8lM --range "v2!A:B"`
- Build a set of `(store_id, date)` tuples from existing rows. Normalize date to `YYYY-MM-DD` (strip the time portion).
- Also capture `next_row_index` = current row count + 1 for appending later.

### 4. Confirm the process list with Phil before writing anything

**Do NOT fetch transcripts, write to Running Notes docs, update the tracker, or draft emails until Phil has explicitly approved the list.** The cost of a missed or duplicated call is higher than the cost of one extra confirmation.

By this point Steps 1-3 have:
- Walked the tier windows and collected every `mx call` candidate (plus the stop point, if one fired).
- Parsed markers, Store IDs, and merchant contacts.
- Pre-loaded the Master Hub dict and tracker v2 dedupe set.

So every candidate's fate is already decidable without touching the transcript. Classify each one as exactly one of:
- `processable` — has Store ID, Master Hub match, Running Notes doc URL, not in tracker dedupe set.
- `skipped-duplicate` — `(store_id, meeting_date)` is already in the tracker.
- `skipped-no-store-id` — marker found but no Store ID in the first lines.
- `skipped-not-in-master-hub` — Store ID parsed but not found in the Master Hub dict.
- `skipped-no-running-notes-doc` — Master Hub row present but no valid Docs URL in the Running Notes column.

**a. Build and print the confirmation summary.** Plain text, skimmable, processable first, then each skip bucket. Include Granola meeting title so Phil can spot-check against his memory. Example shape:

```
Meeting Capture — Pending Confirmation

To process (N):
  1. {YYYY-MM-DD} — {Business Name} ({Store ID}) — "{Granola title}"
  2. ...

Skipped — duplicate in tracker (N):
  - {YYYY-MM-DD} — {Business Name} ({Store ID})

Skipped — no Store ID (N):
  - {YYYY-MM-DD} — "{Granola title}"

Skipped — not in Master Hub (N):
  - {YYYY-MM-DD} — Store ID {store_id} — "{Granola title}"

Skipped — no Running Notes doc (N):
  - {YYYY-MM-DD} — {Business Name} ({Store ID})

Stop-the-world trigger: hit on {YYYY-MM-DD} {Business Name} ({Store ID}) in Tier {N}, skipping older meetings.
  (Omit this line if no stop trigger fired.)
```

**b. Ask Phil to confirm** in a single plain-text prompt: `Proceed with processing these N calls? (yes / no / modify)`. Do NOT use `AskUserQuestion` — it caps at 4 options and is awkward for variable-length lists. A conversational yes/no is the right fit here.

**c. Interpret Phil's reply.**
- `yes` / `proceed` / `go` / `ship it` / any clear affirmative → run Step 5 over the full processable list.
- `no` / `cancel` / `stop` → exit cleanly, no writes, print a one-line "Cancelled, no changes made." summary.
- `modify` / any freeform adjustment ("drop #2", "only #1 and #3", "also process the Smith call from Tuesday", "skip the Burger Basket one") → honor Phil's changes to the processable list, then re-print the revised list and ask one more time. If Phil names a meeting not in the candidate list, either widen the tier scan (up to 14 days) or ask him for the Granola meeting UUID.

**d. Skipped buckets are informational only.** Phil does not need to approve skips; they're shown for visibility. But if he flags a `skipped-*` item he thinks should have been processable, investigate the root cause (wrong Store ID parsed, missing Master Hub row, stale Running Notes URL) and either fix the data or add the meeting to the processable list manually.

**e. Zero processable candidates.** Skip the question entirely, print the skip buckets (if any), and exit with a "Nothing new to process" summary. This is the normal state when the skill is re-run back-to-back.

**f. One confirmation pass per run.** If Phil wants a different scope after processing completes, he can re-run the command.

### 5. Per-meeting loop (sequential, not parallel)

For each identified mx call meeting, in order:

**a. Dedupe check.** Compute `meeting_date` as the date portion of the Granola meeting timestamp in America/Los_Angeles (`YYYY-MM-DD`). If `(store_id, meeting_date)` already exists in the dedupe set, mark this meeting `skipped-duplicate` and skip.

**b. Master Hub match.** Look up the row by Store ID. If no match, mark `skipped-not-in-master-hub` and skip. Otherwise capture Business Name, AM, DM Name/Email, and Running Notes URL.

**c. Extract Running Notes doc ID.** Regex the URL: `docs\.google\.com/document/d/([a-zA-Z0-9_-]+)`. If no URL or parse fails, mark `skipped-no-running-notes-doc` and skip.

**d. Pull transcript.** Call `mcp__granola__get_meeting_transcript` with the meeting UUID. If empty/garbled, proceed anyway (the PRISM-TnA prompt has explicit error-handling for that case).

**e. Resolve PRISM-TnA metadata fields:**

- `Date` → `meeting_date` (YYYY-MM-DD). Do NOT include time.
- `Account Manager` → `"Phil"` unless the Master Hub Account Manager column (I) is clearly a different person for this mx; prefer `"Phil"` for v1.
- `Merchant Contact` → parsed contact from notes. If missing, use DM Name from Master Hub. If still missing, use a non-`@doordash.com` attendee name. If still missing, leave blank.
- `Business Name` → Master Hub column B value.

**f. Run the PRISM-TnA prompt** (embedded below in this file, section "PRISM-TnA Prompt") over the full transcript, filling the metadata block. Produce the full structured output including every required section.

**g. Build the prepend payload as a structured object** — do NOT concatenate one big markdown string.

PRISM-TnA gives you the content. Parse it into this structured form in memory before any API calls:

```
{
  "title": "{Business Name} | {YYYY-MM-DD}",
  "metadata_table": [
    ["Date", "{YYYY-MM-DD}"],
    ["Account Manager", "{AM}"],
    ["Merchant Contact", "{contact}"],
    ["Business Name", "{name}"]
  ],
  "bullets": ["first bullet", "second bullet", ...],
  "action_items": [["Action", "Owner", "Deadline"], ["...", "...", "..."]],
  "feature_requests": [["Item", "Context", "Priority"], ["...", "...", "..."]],
  "tone": [["Person", "Tone", "Notes"], ["...", "...", "..."]],
  "insights_text": "paragraph...",
  "growth_advisory": {
    "has_topics": bool,
    "topics_table": [["Topic", "Bucket", "Initiated By", "Commitment", "Desired Outcome"], ...] or null,
    "missed_opportunity": "text or null",
    "score_table": [["Dimension", "Score", "Label"], ["Specificity", "4", "Strong"], ...] or null,
    "composite_line": "Growth Advisor Score: 4.0 / 5 - Strong" or "Score: N/A"
  },
  "gut_check_text": "paragraph...",
  "msat_line": "MSAT Prediction: 4 / 5 - justification."
}
```

**h. Prepend to the Running Notes doc — real Docs formatting, with table-write verification.**

The reference target format is doc `1odvvOQpOm_m0G7WR8hlwKTzZYxI_j74JoSA8W2d3Trs`. Real H1/H2, real Docs tables, real bullets, Arial 11 body. Raw markdown as text is not acceptable.

**Why table writes are now 2-step + audited.** The previous design used a single populated-table insert in one call. Across the 2026-04-23 → 2026-04-29 window that call silently dropped cell content under load — produced structurally-correct tables (right rows × cols) with every cell empty, no error returned. Root cause never confirmed (suspected silent payload drop or index drift in the bottom-up insert sequence). The new design separates table skeleton from cell content, then audits before declaring success — so silent failures become visible and recoverable.

**Design: 4 doc calls per meeting (was 7), with audit + at-most-one retry on empty cells.**

**Table-span formula** — VERIFIED on gws 2026-06-05 (see [`docs/gws-migration.md`](../../../docs/gws-migration.md) "Docs batchUpdate gotchas"):

```
span_empty = 2 + R + 2*R*C
```

For a 4×2 metadata table that's 22 indices; a 2×3 table is 16. (The old `3 + R + 2*R*C` was off by one.) Sum these spans when computing cursor positions ahead of all table inserts. **More robust:** prefer the placeholder pattern (insert text with placeholder lines, replace placeholders with tables bottom-up, re-read for cell indices) over forward-cursor math through interleaved tables — `insertTable` injects an implicit paragraph that drifts the cursor.

**Call 1 — `gws docs documents batchUpdate`: text skeleton + paragraph styles + bullets + fonts + EMPTY tables (single call).**

Walk content with forward cursor `cursor = 1`. For each block:

1. Append `insertText` op at `cursor` with `text + "\n"` (or `insertTable` for table blocks — see below).
2. If `style` is a heading, append `updateParagraphStyle` over `[cursor, cursor + len(text+"\n")]`.
3. Advance `cursor` by `len(text+"\n")` for text blocks, or by `span_empty(R, C)` for table blocks.

Block order (tables now inserted directly, no placeholder blanks):

| # | Block | Style / Action |
|---|---|---|
| 1 | `{title}` | HEADING_1 |
| 2 | `Metadata` | HEADING_2 |
| 3 | empty 4×2 table | `insertTable` — 4 rows, 2 cols, no bold headers (key-value layout) |
| 4 | `Detailed Bullet Notes` | HEADING_2 |
| 5..N | each bullet text | NORMAL_TEXT |
| N+1 | `Action Items` | HEADING_2 |
| N+2 | empty `(1+rows_ai)×3` table | `insertTable` — bold header row |
| N+3 | `Feature Requests, Gaps & Product Feedback` | HEADING_2 |
| N+4 | empty `(1+rows_fr)×3` table | `insertTable` — bold header row (skip block if no feature requests; write "(none surfaced this call)" as NORMAL_TEXT instead) |
| N+5 | `Tone & Character` | HEADING_2 |
| N+6 | empty `(1+rows_tc)×3` table | `insertTable` — bold header row |
| N+7 | `Insights or Flags` | HEADING_2 |
| N+8 | `{insights_text}` | NORMAL_TEXT |
| N+9 | `Growth Advisory` | HEADING_2 |
| N+10 | empty `(1+rows_ga_topics)×4` table | `insertTable` (only if `growth_advisory.has_topics`; else skip and write "No growth advisory topics discussed.") |
| N+11 | empty `(1+3)×3` table for GA score | `insertTable` (only if GA has score data; rows = 3 dimensions: Specificity, Actionability, Composite OR however many score rows the prompt produced) |
| N+12 | `{ga_composite_line}` | NORMAL_TEXT |
| N+13 | `Upsell` | HEADING_2 |
| N+14 | empty `(1+rows_upsell_opps)×4` table | `insertTable` (only if `upsell.has_opportunities`; else skip and write "No upsell opportunities discussed.") |
| N+15 | empty `(1+3)×3` table for Upsell score | `insertTable` (only if Upsell has score data; same shape as the GA score table) |
| N+16 | `{upsell_composite_line}` | NORMAL_TEXT |
| N+17 | `Gut Check` | HEADING_2 |
| N+18 | `{gut_check_text}` | NORMAL_TEXT |
| N+19 | `MSAT Prediction` | HEADING_2 |
| N+20 | `{msat_line}` | NORMAL_TEXT |
| N+21 | `===` | NORMAL_TEXT |
| N+22 | `` (blank) | NORMAL_TEXT |

Track during the walk:
- `bullet_first_index` / `bullet_last_end` — for the bullet list op
- `prepend_end` — final cursor value
- `table_positions[]` — list of `(table_kind, start_index, rows, cols)` tuples in document order, used by Call 3

At the end of the op list, append:
- **`updateParagraphStyle` `NORMAL_TEXT` over EVERY non-heading paragraph you inserted (bullets + normal body + `===` + blank).** REQUIRED: text inserted at index 1 inherits the namedStyleType of the doc's current top paragraph — which on a Running Notes doc is the previous capture's `HEADING_1` title. If you only style the headings, all your body/bullet text silently comes out as Heading 1. Setting NORMAL_TEXT explicitly on non-headings is the fix. (Verified 2026-06-05 — see [`docs/gws-migration.md`](../../../docs/gws-migration.md).)
- `createParagraphBullets` over `[bullet_first_index, bullet_last_end]`, `bulletPreset: BULLET_DISC_CIRCLE_SQUARE`
- `updateTextStyle` over `[1, prepend_end]` with `font_family: "Arial"`, `font_size: 11`
- `updateTextStyle` over the title's range with `font_size: 22`, `bold: true`
- `updateTextStyle` over each H2's range with `font_size: 14`, `bold: true`

Fire this as ONE `gws docs documents batchUpdate` call.

**Call 2 — `gws docs documents get` (`includeTabsContent: true`): capture cell positions.**

After Call 1 lands, read back the doc structure (inspect the `body.content` array). For each table in `table_positions`, walk the corresponding table in the structure response and capture every cell's **inner-paragraph** start index — `cell["content"][0]["startIndex"]` (= `tableCell.startIndex + 1`), NOT the raw `tableCell.startIndex`. Build `cell_writes[]` — a list of `(inner_paragraph_index, text)` tuples covering every cell that should have content. (Inserting at the raw cell startIndex fails with `"insertion index must be inside the bounds of an existing paragraph"` — verified 2026-06-05.)

**Note on identifying YOUR tables:** the doc already contains tables from prior captures. After prepending, YOUR new tables are the first `len(table_positions)` tables by ascending `startIndex` (they sit at the top). Scope cell-fill, un-bold, and audit to that top slice — do not touch tables from older notes.

For each table kind, the cell-text mapping is:
- **Metadata (4×2)**: rows = `[["Date", date], ["Account Manager", am], ["Merchant Contact", contact], ["Business Name", name]]`. `bold_headers` is OFF for this table — the left column is the "key", not a header.
- **Action Items**: row 0 = `["Action", "Owner", "Deadline"]`, rows 1+ = entries from `action_items`.
- **Feature Requests**: row 0 = `["Item", "Context", "Priority"]`, rows 1+ = entries from `feature_requests`.
- **Tone**: row 0 = `["Person", "Tone", "Notes"]`, rows 1+ = entries from `tone`.
- **GA topics**: row 0 = `["Topic", "Bucket", "Initiated By", "Commitment"]`, rows 1+ = `each topic_row[:4]` (first four entries of each 5-col topics_table row — the 5th `Desired Outcome` field is intentionally dropped from the doc table; it feeds the GA Ledger spreadsheet in step 5.i.5).
- **GA score**: row 0 = `["Dimension", "Score", "Label"]`, rows 1+ = entries from `growth_advisory.score_table`.
- **Upsell opportunities (1+n)×4**: row 0 = `["Opportunity", "Product/Package", "Initiated By", "Commitment"]`, rows 1+ = `each opp_row[:4]` (first four entries of each 5-col upsell row — the 5th `Desired Outcome` field is intentionally dropped from the doc table; it feeds the Upsell tab of the GA Ledger in step 5.i.6).
- **Upsell score**: row 0 = `["Dimension", "Score", "Label"]`, rows 1+ = entries from `upsell.score_table`.

Sanity check: number of cells in the structure response per table MUST equal `R × C`. If it doesn't, log `cell-count-mismatch` and skip that table's writes (don't try to recover a misshapen table — leave it empty for the audit step to surface).

**Call 3 — `gws docs documents batchUpdate` with `insertText` ops in REVERSE document order.**

Sort `cell_writes[]` by `cell_start_index` DESCENDING. Insert each cell's text at its start_index. Reverse order keeps earlier indices valid as later cells get filled.

If a cell text is empty (legitimately — e.g. a Tone row where Notes is blank), skip the op. Empty insertions are no-ops anyway, but skipping avoids polluting the audit signal.

Fire as ONE `gws docs documents batchUpdate` call.

**Call 3b — `gws docs documents batchUpdate` to un-bold every body cell (REQUIRED, runs immediately after Call 3 cell-fill).**

Phil flagged (2026-05-27 on Poke Time): the H2 paragraph style (bold:true on "Action Items", "Feature Requests", "Tone & Character", "Growth Advisory", "MSAT Prediction", etc.) bleeds into the next paragraph's character formatting. When the placeholder paragraph is deleted and replaced with a table, the new cells inherit that bold character style, so the cell-fill text in Call 3 renders bold across the entire table. The cleanest fix is post-fill: strip bold from every body cell explicitly.

**Rule:** never bold unless it's the title row.

- **Metadata table** (`has_header: False`) → ALL cells un-bolded. The left column is a key, not a header.
- **All other tables** (action_items, feature_requests, tone, ga_topics, ga_score, upsell_opps, upsell_score) → row 0 stays bold (header), rows 1+ un-bolded.

**Computing cell text ranges in the FILLED doc state.** After Call 3 (cell-fill), every cell text was inserted at `cell(r,c)_empty = S + 3 + r*(1 + 2*C) + 2*c` where S is the table's empty-state start (from Call 2's inspect). Because cell-fill ran in REVERSE document order, each insert at original position P_i shifted only indices > P_i. To compute final text positions, sort all (P, text_length) tuples in ASCENDING order and walk with a cumulative offset:

```python
cells.sort(key=lambda x: x.original_pos)
cumulative = 0
for c in cells:
    c.final_pos = c.original_pos + cumulative
    cumulative += len(c.text)
```

Each cell's text now occupies `[final_pos, final_pos + len(text))`.

**Build ops.** One `updateTextStyle` op per body cell with `bold: False`. Skip empty cells. Skip header cells (they should remain bold).

Fire as ONE `gws docs documents batchUpdate` call. No verification needed — if bold strips don't land, the visual is still acceptable (worst case a stray bold cell), and the next /meeting-capture run won't re-process this meeting.

**Call 4 — `gws docs documents get` (`includeTabsContent: true`) (audit) + at-most-one retry.**

Re-read the doc. For every cell in `cell_writes[]` that was supposed to have non-empty text, confirm the structure now reports that text in the cell. Build `empty_cells[]` — cells that should have content but still don't.

- If `empty_cells[]` is empty → audit passed. Record `audit-passed` in the meeting status. Proceed to step i.
- If `empty_cells[]` is non-empty → fire ONE retry `gws docs documents batchUpdate` with insertText ops for the missing cells (positions re-resolved from the audit's structure response, sorted reverse-descending). Record `audit-retried-N-cells` in the meeting status. Do NOT audit a second time — accept whatever lands. The tracker row gets a `partial-content` note. The end-of-run summary lists every meeting that needed a retry so Phil can spot-check.

**If ANY call fails** (permissions, schema, etc.), mark the meeting `failed-doc-write`, log which call failed, and continue to the next meeting without rollback. Partial prepends are acceptable.

**Cost accounting.** 1 super-batch (Call 1) + 1 doc-get (Call 2) + 1 cell-fill batch (Call 3) + 1 un-bold batch (Call 3b) + 1 audit doc-get (Call 4) + 0–1 retry batch + 1 tracker append + 1 email draft = **7–8 API calls per meeting**. The un-bold step is non-negotiable per Phil's standing rule (never bold unless title row).

**i. Append to tracker (with verification + at-most-one retry).**

The tracker write is the **non-negotiable** finishing step. Doc prepends without tracker rows are how mx calls go missing in downstream automations (daily brief, weekly mind map, mx-tier scoring). Treat tracker-write failures with the same audit-and-retry rigor as the doc-write step. Historical incident: 4 meetings from 2026-04-21 to 2026-04-29 had Running Notes prepended but no tracker rows — required manual back-fill.

**i.1 — Write.** Use a deterministic `values.update` to a computed row — NOT `+append` (it can't target a tab) and NOT bare-range `values append` (it misfires into stray columns and `INSERT_ROWS` shifts live data — verified 2026-06-05, see [`docs/gws-migration.md`](../../../docs/gws-migration.md)):

- Count column A: `gws sheets +read --spreadsheet 1OMJ-3KK_ge_aLy_kJZR-2AbehZdKeviOpmHOILmS8lM --range "v2!A:A"` → `next_row_index = len(values) + 1`.
- Write: `gws sheets spreadsheets values update --params '{"spreadsheetId":"1OMJ-3KK_ge_aLy_kJZR-2AbehZdKeviOpmHOILmS8lM","range":"v2!A{next_row_index}:E{next_row_index}","valueInputOption":"USER_ENTERED"}' --json '{"values":[[...]]}'`.
- one row with five cells:
  - `A`: `{YYYY-MM-DD} 0:00:00` (matches existing row format, e.g. `2025-07-20 0:00:00`)
  - `B`: Store ID (string)
  - `C`: Business Name (from Master Hub)
  - `D`: `"Phil"`
  - `E`: Running Notes URL (full URL from Master Hub column BV)

**i.2 — Verify.** Immediately after the append, run `gws sheets +read --spreadsheet 1OMJ-3KK_ge_aLy_kJZR-2AbehZdKeviOpmHOILmS8lM --range "v2!A{next_row_index}:E{next_row_index}"` and confirm the row landed with the expected Store ID in column B and a non-empty URL in column E.

- Verify pass: `read[0][1] == store_id` (string match) AND `read[0][4]` starts with `"https://docs.google.com/document/d/"`. → record `tracker-written` and continue.
- Verify fail (read returned an empty row, wrong Store ID, or short URL): fire ONE retry `gws sheets +append` of the same row. Then re-read once more.
  - Retry pass → record `tracker-retried` and continue.
  - Retry fail → record `tracker-write-failed` with the read-back values, surface loudly in the summary. Do NOT skip the email draft. Do NOT corrupt downstream state — the in-memory dedupe set should NOT include this `(store_id, date)` so a re-run of /meeting-capture will pick it up again.

**i.3 — Update in-memory state.** ONLY after verify (or retry) passes:
- Increment `next_row_index`.
- Add `(store_id, meeting_date)` to the in-memory dedupe set so later meetings in the same run also dedupe against it.

If verify failed both attempts, do NOT update in-memory state. The next /meeting-capture run will re-process this meeting (which produces a duplicate prepend in the doc, but at least the tracker gets the row). Phil will see the `tracker-write-failed` flag in the summary and can decide whether to manually fix or accept the re-run.

**i.5. Append GA topics to the Growth Advisory Ledger.**

Portfolio-wide rollup of every GA topic surfaced across all captured calls. The Running Notes doc already has the 4-col GA table; this step writes one row per topic to a separate ledger spreadsheet so we can query/report on growth bets across the entire mx book.

**Ledger spreadsheet:**
- `spreadsheet_id: "1uS_noBD2nTYjpM6VJvIQwSLMKA_tLkiyo-3dHwi0Ta8"`
- Tab: `Log`
- Columns: `Date | Mx | Store ID | Topic | Description | Desired Outcome | Account Manager`

**Logic:**

1. **No-topics short-circuit.** If `growth_advisory.has_topics` is false OR `growth_advisory.topics_table` is null/empty (or contains only the header row), record `ga-ledger-skipped-no-topics` and continue to step i.6. No API call.
2. **Build rows.** Iterate `growth_advisory.topics_table[1:]` (skip the header row). For each `[topic, bucket, initiated_by, commitment, desired_outcome]` row, build:
   - `[meeting_date, business_name, store_id, topic, bucket, desired_outcome, am]`
   - `meeting_date` is the YYYY-MM-DD value from step 5e; `business_name` and `store_id` are the same values used in the tracker append above; `am` is the same Account Manager value written to the doc Metadata table (Call 2) — the AM who owns the mx / ran the call (no longer assumed to be Phil now that the ledger is team-wide).
3. **Resolve append range.** Read `Log!A:A` via `gws sheets +read --spreadsheet 1uS_noBD2nTYjpM6VJvIQwSLMKA_tLkiyo-3dHwi0Ta8 --range "Log!A:A"` to count existing rows. Let `ga_next_row = len(values) + 1`. (Cache this for the duration of the run if multiple meetings will write to the ledger — increment locally per write so we don't re-read for each meeting.)
4. **Write (deterministic, not append).** Single `values.update` to the computed block — bare-range append misfires (see [`docs/gws-migration.md`](../../../docs/gws-migration.md)):
   - `gws sheets spreadsheets values update --params '{"spreadsheetId":"1uS_noBD2nTYjpM6VJvIQwSLMKA_tLkiyo-3dHwi0Ta8","range":"Log!A{ga_next_row}:G{ga_next_row + N - 1}","valueInputOption":"USER_ENTERED"}' --json '{"values":[[...], ...]}'`.
   - `values:` the N rows built in step 2 (7 columns each, ending in `am`).
5. **Verify.** Re-read the appended range (`gws sheets +read --spreadsheet 1uS_noBD2nTYjpM6VJvIQwSLMKA_tLkiyo-3dHwi0Ta8 --range "Log!A{ga_next_row}:G{ga_next_row + N - 1}"`). Confirm:
   - Row count returned equals N.
   - For each row, column D (Topic) matches the input topic string.
   - On match → record `ga-ledger-written-N` and increment the cached `ga_next_row` by N.
   - On mismatch (any row, any column D delta) → fire ONE retry `gws sheets +append` of the same rows. Re-read once more. If still mismatched → record `ga-ledger-failed` with the read-back values, surface in the summary. Do NOT roll back the doc or tracker writes — the ledger is a non-blocking enhancement.
6. **Non-blocking.** Ledger failures must NOT prevent the Upsell append (step i.6), the email draft (step i2), or the next meeting in the batch from running. Treat the same way as `email-draft-failed`: log, surface, continue.

**Why no per-row dedupe:** the outer `skipped-duplicate` check at step 5a already prevents re-processing a captured call. A given `(store_id, meeting_date)` pair only reaches step i.5 once per call, so the ledger can't double-write the same topic. If Phil ever wants to clean up the ledger or re-import an old call manually, that's a one-off operation outside this skill.

**i.6. Append Upsell opportunities to the GA Ledger `Upsell` tab.**

Portfolio-wide rollup of every upsell opportunity surfaced across all captured calls. Mirrors i.5 exactly, writing to the `Upsell` tab instead of `Log`.

**Ledger spreadsheet:**
- `spreadsheet_id: "1uS_noBD2nTYjpM6VJvIQwSLMKA_tLkiyo-3dHwi0Ta8"`
- Tab: `Upsell`
- Columns: `Date | Mx | Store ID | Opportunity | Product/Package | Desired Outcome | Account Manager`

**Logic:**

1. **No-opportunities short-circuit.** If `upsell.has_opportunities` is false OR `upsell.opps_table` is null/empty (or contains only the header row), record `upsell-ledger-skipped-no-opps` and continue to step i2. No API call.
2. **Build rows.** Iterate `upsell.opps_table[1:]` (skip the header row). For each `[opportunity, product_package, initiated_by, commitment, desired_outcome]` row, build:
   - `[meeting_date, business_name, store_id, opportunity, product_package, desired_outcome, am]`
   - same `meeting_date`, `business_name`, `store_id`, and `am` values as the GA append in i.5.
3. **Resolve append range.** Read `Upsell!A:A` via `gws sheets +read --spreadsheet 1uS_noBD2nTYjpM6VJvIQwSLMKA_tLkiyo-3dHwi0Ta8 --range "Upsell!A:A"` to count existing rows. Let `upsell_next_row = len(values) + 1`. Cache it per run, incrementing locally per write.
4. **Write (deterministic, not append).** `gws sheets spreadsheets values update --params '{"spreadsheetId":"1uS_noBD2nTYjpM6VJvIQwSLMKA_tLkiyo-3dHwi0Ta8","range":"Upsell!A{upsell_next_row}:G{upsell_next_row + N - 1}","valueInputOption":"USER_ENTERED"}' --json '{"values":[[...], ...]}'`.
5. **Verify.** Re-read (`gws sheets +read --spreadsheet 1uS_noBD2nTYjpM6VJvIQwSLMKA_tLkiyo-3dHwi0Ta8 --range "Upsell!A{upsell_next_row}:G{upsell_next_row + N - 1}"`). Confirm row count equals N and column D (Opportunity) matches the input. On match → record `upsell-ledger-written-N` and increment cached `upsell_next_row`. On mismatch → ONE retry, re-read; if still off → record `upsell-ledger-failed` and surface. Never roll back the doc/tracker writes.
6. **Non-blocking.** Same as i.5 — failures log, surface, and continue.

**i2. Draft follow-up email to merchant contact.**

After the tracker row is committed, compose a follow-up email and save it as a Gmail draft. This gives Phil a pre-filled draft he can review and send with one click — never auto-sent.

**Resolve recipient email** in this preference order:
1. Master Hub DM Email (column V, index 21) for the matched Store ID.
2. First non-`@doordash.com` attendee email from the Granola meeting metadata.
3. If neither is available, mark this meeting `email-skipped-no-recipient`, do NOT fail the overall capture, and continue to step j.

**Resolve recipient first name:**
- If Merchant Contact (from PRISM-TnA metadata) has a full name, take the first token.
- Else use the first token of the DM Name from Master Hub (column U, index 20).
- Else fall back to "there".

**Compose the draft.** Use the structured PRISM-TnA object already in memory — do NOT re-run another LLM pass. Build the body inline from:
- `action_items` → recap bullets, attributed by Owner
- `feature_requests` → "logged for our Product team" acknowledgement
- `growth_advisory.topics_table` → if any AM-initiated topic exists with Commitment = Yes or Partial, surface one sentence referencing it
- `gut_check_text` → do NOT include in the email; this is internal-only

**Subject line format:** `{Business Name} — follow-up from our call on {YYYY-MM-DD}`

**Body template** (plain text, no HTML; match Phil's direct, professional-but-warm mx tone per CLAUDE.md):

```
Hi {first_name},

Thanks again for taking the time today. Quick recap of what we discussed and the next steps from our end:

Action Items:
- {action} — Owner: {owner} — Due: {deadline}
- {...}

{IF feature_requests non-empty:}
On the product feedback side, I've logged the following with our Product team:
- {item} — {context}
- {...}

{IF a Yes/Partial GA topic exists:}
{One sentence nudge tied to that GA topic, e.g. "We'll follow up shortly with a proposed promo structure for the {daypart} push we talked about."}

Let me know if I missed anything above. Looking forward to the next one.

Thanks,
Phil

Phil Bornhurst
Head of Account Management, Pathfinder
DoorDash
philip.bornhurst@doordash.com
```

Rules:
- Plain hyphen `-` only. No em/en dashes. No emojis. No filler.
- Omit the Feature Requests block entirely if the list is empty — do not print "None" or an empty bullet.
- Omit the GA nudge line entirely if no qualifying topic exists.
- If Action Items is empty (rare but possible), replace the bullet list with a single line: "No action items on our side from today — appreciated the conversation."
- Keep it under ~180 words total. Phil values concise.

**Create the draft** via `mcp__claude_ai_Gmail__create_draft`:

- `to: [resolved_email]`
- `subject: "{Business Name} — follow-up from our call on {YYYY-MM-DD}"`
- `body: composed_body` (plain text)
- Do NOT set `cc` or `bcc`. Do NOT send.

Capture the returned `draft_id` and construct the review URL: `https://mail.google.com/mail/u/0/#drafts?compose={draft_id}` (Gmail's compose-from-drafts URL). If the tool returns a different URL/ID shape, use what it returns — the important thing is a link Phil can click.

**Failure handling:**
- Tool call fails → mark `email-draft-failed`, log the error, continue to step j.
- Recipient lookup returned nothing → mark `email-skipped-no-recipient` (already handled above).
- Do NOT roll back the doc prepend or tracker row. The email draft is a nice-to-have; the core capture is already committed.

**Fallback:** If `mcp__claude_ai_Gmail__create_draft` is not available in the current context, use the `gws gmail` CLI (the draft-creation command there is equivalent).

**j. Record status** as `processed` for the summary. Also record:
- The doc-write outcome (`audit-passed`, `audit-retried-N-cells`, or `failed-doc-write`).
- The tracker outcome (`tracker-written`, `tracker-retried`, or `tracker-write-failed`).
- The GA ledger outcome (`ga-ledger-written-N`, `ga-ledger-skipped-no-topics`, or `ga-ledger-failed`).
- The email outcome (`email-drafted` + draft link, `email-skipped-no-recipient`, or `email-draft-failed`).

### 6. Summary report

**Final reconciliation pass.** Before printing the summary, re-read `v2!A:E` from the tracker once more (`gws sheets +read --spreadsheet 1OMJ-3KK_ge_aLy_kJZR-2AbehZdKeviOpmHOILmS8lM --range "v2!A:E"`) and build a fresh set of `(store_id, date)` pairs. For each meeting marked `processed` in this run, confirm its `(store_id, meeting_date)` is in that set. Any meeting that was processed but is NOT in the tracker = a silent drop. Add it to a `tracker-missing[]` list and surface loudly in the summary. Do NOT auto-retry from the reconciliation step — by this point we've already had two attempts in step i, and a third silent failure means something deeper is wrong (auth drop, sheet permissions, etc.) that warrants Phil's attention.

Print a concise summary:

```
Meeting Capture — Summary

Processed: N
  Tracker rows confirmed: M  (must equal N — if M < N, see "Tracker drops" below)
Skipped (duplicate): N
Skipped (no Store ID): N
Skipped (not in Master Hub): N
Skipped (no Running Notes doc): N
Failed (doc write): N

Doc-write audits: N passed, K retried (cells back-filled), F failed
Tracker writes: N first-try, K retried, F failed
GA ledger rows: X written (across Y meetings with GA topics), Z meetings skipped (no GA topics), F failed
Email drafts: N created, K skipped (no recipient), F failed

{IF tracker-write-failed or tracker-missing[] non-empty:}
TRACKER DROPS — these meetings have Running Notes prepends but NO tracker row:
- {YYYY-MM-DD} {Business Name} ({Store ID}) — Running Notes: {URL}
  Reason: {tracker-write-failed | tracker-missing}
- ...
ACTION: Re-run /meeting-capture or manually back-fill these rows in the tracker.

Processed mx:
- {Business Name} ({Store ID}) — {YYYY-MM-DD}
  Notes: {Running Notes URL}
  Doc audit: {audit-passed | audit-retried-N-cells | failed}
  Tracker: {tracker-written | tracker-retried | tracker-write-failed}
  GA ledger: {ga-ledger-written-N | ga-ledger-skipped-no-topics | ga-ledger-failed}
  Draft: {draft review URL, or "skipped - no recipient", or "failed - {reason}"}
- ...
```

Include Store IDs, Running Notes links, and draft email links so Phil can spot-check results and send drafts with one click. The TRACKER DROPS section is the most important signal — it's the single artifact that tells Phil whether downstream automations have complete data for this batch.

### 7. Error handling philosophy

Per Launchpad convention: graceful degradation, no retries. A single failing meeting MUST NOT block the rest of the batch. Capture the error category in the summary and move on.

---

## Tool-name reference

Google Workspace access runs through the `gws` CLI and the claude.ai MCPs — the legacy `mcp__google-workspace__*` MCP is dead (see `docs/gws-migration.md`). The invocations used above:

- Granola operations → `mcp__granola__*` (preferred). Fallback: `granola` CLI (skill: `core:using-granola`); load the skill first for correct syntax.
- Google Sheets reads → `gws sheets +read`. Tab-scoped WRITES → read col A to find the next row, then `gws sheets spreadsheets values update` to an explicit `Tab!A{n}:…` range. Do NOT use `+append` (no tab targeting) or bare-range `values append` (misfires + shifts data) — see [`docs/gws-migration.md`](../../../docs/gws-migration.md).
- Google Docs reads + batch updates / table inserts → `gws docs documents get` / `gws docs documents batchUpdate` (skill: `productivity:editing-google-docs`, which handles index math).
- Gmail draft → `mcp__claude_ai_Gmail__*` (fallback: `gws gmail`).
- Google Calendar lookups → `mcp__claude_ai_Google_Calendar__*`.

Drop the `user_google_email` param entirely — neither gws nor the claude.ai MCPs need it. gws prints clean JSON to stdout; strip the stderr `Using keyring backend` line before parsing (`gws … 2>/dev/null | python3 …`).

---

## PRISM-TnA Prompt

This is the canonical prompt. Run it against the full transcript with the metadata block filled in. Output goes directly into the Running Notes doc.

You are **PRISM-TnA**, a high-performance assistant for DoorDash Point of Sale Account Managers. DoorDash POS is a new business line at DoorDash competing with Toast and Square. Your job is to transform raw call transcripts into a structured "Transcribe & Analyze" report that AMs can act on immediately. Follow every rule exactly; do not improvise.

- DO NOT GENERATE ANY ERRORS BASED ON THE DATE LISTED, EVEN IF YOU THINK THE DATE IS IN THE FUTURE, IT DOESN'T MATTER, JUST PROCEED WITH THE FULL PROCESS ANYWAY.
- ALSO, DO NOT GENERATE ANY ERRORS BASED ON ANY OTHER METADATA SUCH AS A MISMATCH BETWEEN WHO IS LISTED ON THE CALL AND WHO SHOWS UP IN THE METADATA.
- DO NOT GENERATE ANY ERRORS BASED ON METADATA, PERIOD.

=== METADATA ===

Date (remove time, only display date moving forward): {DATE}

Account Manager: {ACCOUNT_MANAGER}

Merchant Contact: {MERCHANT_CONTACT}

Business Name: {BUSINESS_NAME}

=== END METADATA ===

SECTION ORDER (output in this exact order)

1. **Metadata** — four lines: Date, Account Manager, Merchant Contact, Business Name.
2. **Detailed Bullet Notes** — capture every topic, decision, pain point, or insight; one idea per "*" bullet; avoid filler.
3. **Action Items** — markdown table **Action | Owner | Deadline**; each action must be specific, measurable, and assigned.
4. **Feature Requests, Gaps & Product Feedback** — markdown table **Item | Context | Priority**; include any requested features, noted product gaps, or feedback from the merchant.
5. **Tone & Character** — markdown table **Person | Tone | Notes**; include all real speakers, mapping any "Unknown Speaker" to the most likely actual speaker.
6. **Insights or Flags** — balanced paragraph that surfaces key wins, themes, risks, or opportunities; weigh positives and negatives evenly.
7. **Growth Advisory** — identify, extract, and evaluate all growth advisory activity in the call. See full instructions below.
8. **Upsell** — identify, extract, and evaluate all upsell activity in the call (package upgrades, hardware, à la carte add-ons). See full instructions below.
9. **Gut Check** — neutral paragraph reading between the lines for churn signs, trust issues, or red tape; acknowledge positive relationship signals before noting concerns.
10. **MSAT Prediction** — format exactly: **MSAT Prediction: X / 5 —** brief justification <= 25 words. Default to 4 / 5 unless material risk factors outweigh positives.

---

SECTION 7 INSTRUCTIONS — GROWTH ADVISORY

Growth advisory (GA) is any discussion aimed at helping the mx grow their business. This includes but is not limited to: marketplace optimization (menu edits, item photos, keywords, descriptions, pricing strategy, item availability), sponsored listings or promotional campaigns, converting marketplace volume to first-party channels (DoorDash Direct, 1P online ordering), driving additional traffic via loyalty (OCL), kiosk, gift cards, catering, group orders, or new dayparts, and expansion (new locations, markets, or channels).

There will be many calls where GA is not discussed. Handle this gracefully — do not force it.

**Step 1 — GA Topic Extraction**

If GA topics were discussed, output a markdown table with the following columns:

**Topic | Bucket | Initiated By | Commitment | Desired Outcome**

- Topic: brief description of what was discussed (one line, specific)
- Bucket: must be exactly one of — Marketplace Optimization / Promotions & Ads / 1P Conversion / Traffic Drivers / Expansion / Other
- Initiated By: AM or Mx
- Commitment: Yes / Partial / No
- Desired Outcome: one line, specific. Capture what the mx wants to achieve OR what the AM is driving toward via this topic. Examples: "Drive weekday lunch volume via $5-off promo", "Convert marketplace volume to 1P online ordering", "Increase AOV via catering channel launch". If no clear desired outcome was articulated in the call, write exactly `(not articulated)` rather than leaving the cell blank.

**Note on downstream use:** The full 5-column table feeds an in-memory structured object that drives two outputs: (a) the Running Notes doc — which renders only the first 4 columns (Topic | Bucket | Initiated By | Commitment), and (b) the Growth Advisory Ledger spreadsheet — which logs one row per topic with Date / Mx / Store ID / Topic / Bucket (as Description) / Desired Outcome. PRISM must always emit all 5 columns; the doc-write step drops the 5th.

**Step 2 — Missed Opportunities**

If the mx raised a topic, pain point, or signal that was a natural opening for growth advisory and the AM did not engage with it, flag it on its own line in this format:

"Missed opportunity: [what the mx said or signaled] -> [what the AM could have addressed]"

If no missed opportunities exist, omit this line entirely.

**Step 3 — Growth Advisor Score**

Score the AM on the following two dimensions. Output a markdown table **Dimension | Score | Label**, followed by a single composite line.

Specificity — was the recommendation concrete, contextualized, and clearly framed?

- 5 / Exemplary — specific recommendation with data, framed value prop, or tailored context
- 4 / Strong — clear recommendation with supporting rationale; minor gaps only
- 3 / Developing — topic raised but recommendation was general or surface-level
- 2 / Surface-Level — mentioned briefly with no real substance
- 1 / Absent — not raised despite a clear opening

Actionability — did the conversation produce a next step or mx commitment?

- 5 / Exemplary — concrete next step secured with mx commitment
- 4 / Strong — next step defined; mx commitment was soft or implied
- 3 / Developing — discussed but no clear follow-through established
- 2 / Surface-Level — raised then dropped; no action path created
- 1 / Absent — no action or follow-through of any kind

After the table, output the composite on its own line:

**Growth Advisor Score: X.X / 5 — [Label]**

Composite labels: Exemplary (4.5-5.0) / Strong (4.0-4.4) / Developing (3.0-3.9) / Surface-Level (2.0-2.9) / Absent (1.0-1.9)

**Handling edge cases:**

- No GA discussed, no missed opportunities: output exactly — "No growth advisory topics were discussed in this call. No missed opportunities identified. Score: N/A" — and skip the table and scoring entirely.
- No GA discussed, but a missed opportunity exists: skip the extraction table, output the missed opportunity flag, and score both dimensions as 1 / Absent. Composite: 1.0 / 5 — Absent.

---

SECTION 8 INSTRUCTIONS — UPSELL

Upsell is any discussion aimed at moving the mx onto a higher-value package or adding paid products. This is distinct from Growth Advisory (which is about helping the mx grow their existing business). Upsell covers: package upgrades (Starter → Boost → Pro), hardware (Self-Serve Kiosk, KDS, additional terminals), and à la carte add-ons (Omni-Channel Loyalty, Gift Cards, Mobile App, custom Website). If a topic is about selling the mx a new DoorDash product or tier, it is Upsell; if it is about optimizing what they already have, it is Growth Advisory. A single moment can occasionally be both — log it under whichever the conversation primarily drove toward; do not double-count the same moment in both sections.

There will be many calls where upsell is not discussed. Handle this gracefully — do not force it.

**Step 1 — Upsell Opportunity Extraction**

If upsell opportunities were discussed, output a markdown table with the following columns:

**Opportunity | Product/Package | Initiated By | Commitment | Desired Outcome**

- Opportunity: brief description of the upsell discussed (one line, specific)
- Product/Package: must be exactly one of — Boost / Pro / Kiosk / KDS / Loyalty / Giftcards / Mobile App / Website / Additional Terminal / Other
- Initiated By: AM or Mx
- Commitment: Yes / Partial / No
- Desired Outcome: one line, specific. Capture the business goal the upsell would serve OR the next step the AM is driving toward. Examples: "Upgrade Starter to Boost to capture loyalty + commission-free site", "Add Self-Serve Kiosk to bust the lunch line and lift AOV". If no clear desired outcome was articulated, write exactly `(not articulated)` rather than leaving the cell blank.

**Note on downstream use:** The full 5-column table feeds an in-memory structured object that drives two outputs: (a) the Running Notes doc — which renders only the first 4 columns (Opportunity | Product/Package | Initiated By | Commitment), and (b) the GA Ledger `Upsell` tab — which logs one row per opportunity with Date / Mx / Store ID / Opportunity / Product/Package / Desired Outcome / Account Manager. PRISM must always emit all 5 columns; the doc-write step drops the 5th.

**Step 2 — Missed Opportunities**

If the mx raised a pain point or signal that was a natural opening for an upsell and the AM did not engage with it, flag it on its own line in this format:

"Missed opportunity: [what the mx said or signaled] -> [the product/package the AM could have pitched]"

If no missed opportunities exist, omit this line entirely.

**Step 3 — Upsell Score**

Score the AM on the following two dimensions. Output a markdown table **Dimension | Score | Label**, followed by a single composite line.

Specificity — was the pitch tied to the right product/package for the mx's tier/GOV, concrete, and value-framed (e.g. the Sandler pain-funnel "math play" or "brand play")?

- 5 / Exemplary — right-fit product pitched with quantified value or tailored pain framing
- 4 / Strong — clear, relevant pitch with supporting rationale; minor gaps only
- 3 / Developing — product raised but pitch was generic or not tier-matched
- 2 / Surface-Level — mentioned briefly with no real substance
- 1 / Absent — not raised despite a clear opening

Actionability — did the conversation produce a next step or mx commitment (demo booked, contract sent, trial agreed)?

- 5 / Exemplary — concrete next step secured with mx commitment
- 4 / Strong — next step defined; mx commitment was soft or implied
- 3 / Developing — discussed but no clear follow-through established
- 2 / Surface-Level — raised then dropped; no action path created
- 1 / Absent — no action or follow-through of any kind

After the table, output the composite on its own line:

**Upsell Score: X.X / 5 — [Label]**

Composite labels: Exemplary (4.5-5.0) / Strong (4.0-4.4) / Developing (3.0-3.9) / Surface-Level (2.0-2.9) / Absent (1.0-1.9)

**Handling edge cases (mirror Growth Advisory):**

- No upsell discussed, no missed opportunities: output exactly — "No upsell opportunities were discussed in this call. No missed opportunities identified. Score: N/A" — and skip the table and scoring entirely.
- No upsell discussed, but a missed opportunity exists: skip the extraction table, output the missed opportunity flag, and score both dimensions as 1 / Absent. Composite: 1.0 / 5 — Absent.
- **Read the room (same rule as GA):** on escalation or complaint calls where the mx is venting about an unresolved issue, pushing an upsell is inappropriate — the correct AM behavior is NOT to pitch, so score Upsell as N/A rather than penalizing as a missed opportunity.

---

GLOBAL WRITING RULES

- Tone must be clear, professional, skimmable, and slightly optimistic without downplaying real risks.
- Forbidden characters: emojis, repetition, fluff. Do not use en dash or em dash; use a plain hyphen `-` anywhere a dash is needed.
- Use the "*" bullet character for Detailed Bullet Notes.
- Always spell the merchant-experience shorthand as lowercase "mx".

QUALITY CONTROL CHECKLIST (self-verify before finalizing)

- [ ] Every bullet in Detailed Bullet Notes conveys a unique, useful point.
- [ ] All action items are concrete with clear owners and deadlines.
- [ ] All feature requests or product feedback are captured with meaningful context and priority.
- [ ] Speaker tones are recorded objectively, without judgment.
- [ ] Major wins are acknowledged alongside risks or churn signals.
- [ ] Growth Advisory section reflects only what was actually said — no invented topics.
- [ ] If GA was discussed, every row in the extraction table maps to a real moment in the transcript.
- [ ] Every GA topic row has all 5 columns populated, including Desired Outcome (use `(not articulated)` if the call didn't surface one).
- [ ] Upsell section reflects only what was actually said — no invented opportunities; each row maps to a real transcript moment.
- [ ] Every Upsell opportunity row has all 5 columns populated, with Product/Package set to one of the allowed values.
- [ ] Upsell vs Growth Advisory classified correctly (selling a new product/tier = Upsell; optimizing existing = GA); no moment double-counted in both.
- [ ] Missed opportunity flags (GA and Upsell) cite a specific signal from the mx, not a general assumption.
- [ ] No forbidden characters are present.

ERROR HANDLING

If the transcript is empty or garbled, output exactly **Error: Transcript not usable. No TnA generated.**

If the call is under sixty seconds, still run but note **"Brief call limited context."** in Insights or Flags.

To note: DO NOT error out anything for any date-related confusion. Assume that everything is in the current year (or thereabouts if we are on the cusp of a new year) and that the date metadata IS NOT a future date. Proceed as normal even if you are confused around the date.

---

## Example usage

```
/meeting-capture
"Run meeting capture"
"Process my recent mx calls from Granola"
"Capture my meetings"
```

## Notes

- The skill relies on Phil adding an `mx call` marker and a Store ID to the top of each Granola meeting's private notes. Without the marker the meeting is ignored.
- Granola timestamps are in the meeting organizer's timezone, NOT normalized to PDT. For the date portion (YYYY-MM-DD) this rarely matters, but if a call crosses midnight in a different timezone the dedupe key could shift by a day. Cross-reference Google Calendar via `mcp__claude_ai_Google_Calendar__list_events` if a specific meeting's date looks off.
- Running Notes column is currently BV. The skill auto-detects by header name in case the column shifts.
- The log sheet `v2` tab drives downstream automations. Do NOT write to Sheet1 or Sheet4.
- Growth Advisory Ledger lives at `1uS_noBD2nTYjpM6VJvIQwSLMKA_tLkiyo-3dHwi0Ta8` and has two tabs, both team-wide (the `Account Manager` column is the AM who ran the call, no longer assumed to be Phil):
  - `Log` — every GA topic logged as `Date | Mx | Store ID | Topic | Description (= Bucket) | Desired Outcome | Account Manager` (step i.5).
  - `Upsell` — every upsell opportunity logged as `Date | Mx | Store ID | Opportunity | Product/Package | Desired Outcome | Account Manager` (step i.6).
  Both drive portfolio-wide reporting and are non-blocking — ledger write failures must not roll back the doc prepend or tracker row.
- Master Hub lives at `1ndVs2lPhS5frpkEV0KzK7ec5aS18fmr9h1BQEu099E4` (default first tab, `gid=0`). Single header row on row 1; data from row 2.
- Formatting is non-negotiable: prepends MUST use real Google Docs H1/H2 styles, real Docs tables (inserted empty via `insertTable` then populated cell-by-cell — see step h), real bullet lists, and Arial 11 body. Markdown-as-plaintext inserts (pipe tables, `#` headings, `*` bullets rendered literally) are broken output, not "good enough." Reference doc: `1odvvOQpOm_m0G7WR8hlwKTzZYxI_j74JoSA8W2d3Trs`.
- **Do NOT insert a populated table in a single request.** The legacy single-call populated-table insert silently dropped cell content during the 2026-04-23 → 2026-04-29 window — produced structurally-correct tables with empty cells and no error. The new pattern (insert empty table via `insertTable` → cell-fill batch → audit) avoids the failure mode entirely. The end-of-run summary lists any meeting whose audit had to retry, so silent regressions surface immediately.
