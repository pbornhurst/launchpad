---
name: meeting-capture
description: Scan recent Granola meetings for mx calls, generate structured PRISM-TnA notes from the transcript, prepend them to the mx's Running Notes doc, and log the call to the Running Notes Input Tracker. Trigger on "run meeting capture", "capture my meetings", "process my recent mx calls", "capture granola meetings", "prepend meeting notes to running notes", "log my recent calls", or /meeting-capture. Scans and classifies every candidate first, then confirms the process list with Phil before writing anything.
---

# meeting-capture — Capture Granola mx Calls to Running Notes

Scan recent Granola meetings for mx calls, generate structured PRISM-TnA notes from the transcript, prepend them to the mx's Running Notes doc, and log the call to the Running Notes Input Tracker.

**Confirms before writing.** Scans in tiered time windows (2h → 12h → 24h → 48h → 7d), stops the moment it hits an mx call that's already in the tracker, classifies every candidate (processable vs. skipped), then waits for Phil's explicit go-ahead before touching any doc or tracker. Re-running back-to-back is cheap (usually bails after Tier 1).

## Instructions

### 1. Scan Granola in tiered time windows (newest first)

**Goal:** Do as little work as possible. Check the most recent meetings first and stop scanning as soon as we hit a meeting that was already captured.

**1a. One-shot meeting list.** Call `mcp__granola__list_meetings` with `time_range: "last_30_days"` (Granola has no native < 1 week window). This is cheap — a single call returning up to 25 meeting summaries.

**1b. Sort newest-first** by `created_at` (or `start_at`) and compute each meeting's age in hours relative to `now()` in America/Los_Angeles. Use `date` (bash) or `datetime` (python) — never guess hour offsets. Remember Granola timestamps render in the event creator's timezone, not PDT (see MEMORY.md Granola notes).

**1c. Tier windows.** Walk the list in the following tiered windows, from narrowest to widest:

1. **Tier 1** — last **2 hours**
2. **Tier 2** — last **12 hours** (delta: 2h → 12h, only meetings not already fetched in Tier 1)
3. **Tier 3** — last **24 hours**
4. **Tier 4** — last **48 hours**
5. **Tier 5** — last **168 hours (7 days)**

For each tier:
- Collect the meetings in that tier's delta window whose notes have NOT yet been fetched.
- Batch-fetch their notes via `mcp__granola__get_meetings` (up to 10 IDs per call).
- Walk each meeting in newest-first order, run marker detection (Step 2), and append classified candidates to the in-memory candidate list. **Do not fetch transcripts and do not write to Docs / tracker / Gmail yet** — that happens in Step 5 after Phil confirms the list.
- **Stop-the-world trigger:** The moment you encounter an `mx call` meeting whose `(store_id, meeting_date)` is already in the tracker dedupe set (Section 3), halt all further tier expansion. Everything older is presumed already processed. Record this as the stop point for the confirmation summary.
- If no stop-the-world trigger fires within this tier, expand to the next tier.

**1d. How the dedupe signal works.** Before Tier 1 runs, load the tracker v2 dedupe set ONCE (Section 3). Every successfully captured meeting in the current run also gets added to the in-memory dedupe set so it short-circuits subsequent tiers. The tracker is append-only, so a `(store_id, date)` pair found there means that exact mx call was already captured — nothing older could plausibly be new.

**1e. Edge cases:**
- Non-`mx call` meetings (no marker) do NOT count toward the stop trigger. Skip them and keep walking.
- `mx call` meetings that are missing a Store ID, not in Master Hub, or have no Running Notes doc count as `skipped-*` but DO NOT trigger stop — they weren't captured, so we have no signal that older meetings were either.
- If Tier 5 completes with zero captures and zero stop hits, the summary should note "no new mx calls in last 7 days" — this is the true base case.

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

- `mcp__google-workspace__read_sheet_values`
  - `spreadsheet_id: "1ndVs2lPhS5frpkEV0KzK7ec5aS18fmr9h1BQEu099E4"`
  - `range_name: "A1:CA1"`
  - `user_google_email: "philip.bornhurst@doordash.com"`
- Locate the column index where header equals exactly `"Running Notes"`. Expected: column BV (index 73). If it has moved, use the discovered column.

**Master Hub body.** The `read_sheet_values` tool display-truncates at ~50 rows even on successful larger reads, which makes per-row lookups flaky. Instead:

- Call `mcp__google-workspace__get_drive_file_download_url` with `file_id: "1ndVs2lPhS5frpkEV0KzK7ec5aS18fmr9h1BQEu099E4"` and `export_format: "xlsx"`.
- Parse the downloaded `.xlsx` with Python + `openpyxl` (install via `pip3 install openpyxl --break-system-packages` if needed). Use the first/default sheet. Headers on row 1, data from row 2.
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

- `mcp__google-workspace__read_sheet_values`
  - `spreadsheet_id: "1OMJ-3KK_ge_aLy_kJZR-2AbehZdKeviOpmHOILmS8lM"`
  - `range_name: "v2!A:B"`
  - `user_google_email: "philip.bornhurst@doordash.com"`
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
    "topics_table": [["Topic", "Bucket", "Initiated By", "Commitment"], ...] or null,
    "missed_opportunity": "text or null",
    "score_table": [["Dimension", "Score", "Label"], ["Specificity", "4", "Strong"], ...] or null,
    "composite_line": "Growth Advisor Score: 4.0 / 5 - Strong" or "Score: N/A"
  },
  "gut_check_text": "paragraph...",
  "msat_line": "MSAT Prediction: 4 / 5 - justification."
}
```

**h. Prepend to the Running Notes doc — real Docs formatting, minimal API cost.**

The reference target format is doc `1odvvOQpOm_m0G7WR8hlwKTzZYxI_j74JoSA8W2d3Trs`. Real H1/H2, real Docs tables, real bullets, Arial 11 body. Raw markdown as text is not acceptable.

**Design constraint: 3 API calls per meeting, zero intermediate `inspect_doc_structure` calls.** Positions are precomputed with the table-span formula below and applied in a single order-sensitive pipeline.

**Table-span formula.** A `create_table_with_data` insert at position `P` with `R` rows × `C` cols and `S` total characters of cell content (sum of `len(cell)` across all cells, no newlines counted) occupies this many indices:

```
span = 3 + R + 2*R*C + S
```

Derivation (verified empirically on a 4×2 / 90-char-content table that shifted subsequent indices by 113): 3 bytes for the table header/footer structural tokens, `R` bytes for row markers, 2 bytes per cell for the cell marker plus its paragraph's trailing newline, plus the raw content chars.

Use this to precompute, ahead of Call 1, exactly where every future position lands after all 6 tables are inserted.

**Call 1 — `batch_update_doc`: text skeleton + paragraph styles + bullets + fonts (single call, all at pre-table positions).**

Why at pre-table positions: format operations on a range attach character formatting to those characters. Subsequently inserting tables shifts the characters to higher indices but they retain the formatting. So applying bullets and font to the original range works — the formatting moves with the text.

Walk the content in document order with a forward cursor starting at `cursor = 1`. For each block `(text, style)`:

1. Append `insert_text` op at `cursor` with `text + "\n"`.
2. If `style` is a heading, append `update_paragraph_style` over `[cursor, cursor + len(text+"\n")]` with the named style.
3. `cursor += len(text + "\n")`.

Block order (same as before, with placeholder blank lines where tables will land):

| # | Text | Style |
|---|---|---|
| 1 | `{title}` | HEADING_1 |
| 2 | `Metadata` | HEADING_2 |
| 3 | `` (blank) | NORMAL_TEXT — metadata table placeholder |
| 4 | `Detailed Bullet Notes` | HEADING_2 |
| 5-N | each bullet text | NORMAL_TEXT |
| N+1 | `Action Items` | HEADING_2 |
| N+2 | `` (blank) | NORMAL_TEXT — action items table placeholder |
| N+3 | `Feature Requests, Gaps & Product Feedback` | HEADING_2 |
| N+4 | `` (blank) | NORMAL_TEXT — placeholder |
| N+5 | `Tone & Character` | HEADING_2 |
| N+6 | `` (blank) | NORMAL_TEXT — placeholder |
| N+7 | `Insights or Flags` | HEADING_2 |
| N+8 | `{insights_text}` | NORMAL_TEXT |
| N+9 | `Growth Advisory` | HEADING_2 |
| N+10..11 | blank placeholders for GA topics + GA score (only if GA has data; else skip both and write the "No GA discussed" paragraph directly) | NORMAL_TEXT |
| N+12 | `{ga_composite_line}` | NORMAL_TEXT |
| N+13 | `Gut Check` | HEADING_2 |
| N+14 | `{gut_check_text}` | NORMAL_TEXT |
| N+15 | `MSAT Prediction` | HEADING_2 |
| N+16 | `{msat_line}` | NORMAL_TEXT |
| N+17 | `===` | NORMAL_TEXT |
| N+18 | `` (blank) | NORMAL_TEXT |

Track during this walk:
- `bullet_first_index` = start_index of first bullet paragraph
- `bullet_last_end` = end_index of last bullet paragraph
- `prepend_end` = final cursor value

At the end of the op list for Call 1, append these operations (all referencing the positions just computed, which are still valid because no tables have been inserted yet):

- `create_bullet_list` over `[bullet_first_index, bullet_last_end]`, `list_type: UNORDERED`
- `format_text` over `[1, prepend_end]` with `font_family: "Arial"`, `font_size: 11`
- `format_text` over the title's range with `font_size: 22`, `bold: true` (H1 override — named style alone doesn't carry font size in this tool)
- `format_text` over each H2's range with `font_size: 14`, `bold: true`

Fire this as ONE `batch_update_doc` call.

**Calls 2-7 — `create_table_with_data` × 6, bottom-up.**

Insert tables in DESCENDING placeholder-index order so earlier placeholders' indices remain valid as later tables are inserted. Given the placeholder positions tracked in Call 1, the order is typically:

1. GA score placeholder (highest index)
2. GA topics placeholder
3. Tone & Character placeholder
4. Feature Requests placeholder
5. Action Items placeholder
6. Metadata placeholder (lowest index)

For each table:

```
mcp__google-workspace__create_table_with_data
  document_id: {doc_id}
  user_google_email: philip.bornhurst@doordash.com
  tab_id: t.0                         # or the actual tab id if different
  index: {placeholder.start_index}
  bold_headers: true                  # false for Metadata (key-value, not tabular)
  table_data: [[headers], [row], ...]
```

Because bullets and font were applied to the original range in Call 1, the formatting stays with the text as tables push it down. Tables get their own default formatting, which is fine — the Launchpad reference doc's tables are not specially formatted beyond bold headers.

**Call 8 — `modify_sheet_values` to append the tracker row** (unchanged from step i below).

**Cost accounting.** 1 super-batch + 6 table inserts + 1 tracker append + 1 email draft = 9 API calls per meeting. No `inspect_doc_structure` calls required. If GA has no topics and score, the table count drops to 4 and total calls drop to 7. If the email step skips (no recipient available), subtract 1.

**If ANY call fails** (permissions, schema, etc.), mark the meeting `failed-doc-write`, log which call failed, and continue to the next meeting without rollback. Partial prepends are acceptable.

**i. Append to tracker.** Use `mcp__google-workspace__modify_sheet_values`:

- `spreadsheet_id: "1OMJ-3KK_ge_aLy_kJZR-2AbehZdKeviOpmHOILmS8lM"`
- `range_name: "v2!A{next_row_index}:E{next_row_index}"`
- `user_google_email: "philip.bornhurst@doordash.com"`
- `value_input_option: "USER_ENTERED"`
- `values:` one row with five cells:
  - `A`: `{YYYY-MM-DD} 0:00:00` (matches existing row format, e.g. `2025-07-20 0:00:00`)
  - `B`: Store ID (string)
  - `C`: Business Name (from Master Hub)
  - `D`: `"Phil"`
  - `E`: Running Notes URL (full URL from Master Hub column BV)

After successful write, increment `next_row_index` and add `(store_id, meeting_date)` to the in-memory dedupe set so later meetings in the same run also dedupe against it.

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

**Create the draft** via `mcp__google-workspace__draft_gmail_message`:

- `user_google_email: "philip.bornhurst@doordash.com"`
- `to: [resolved_email]`
- `subject: "{Business Name} — follow-up from our call on {YYYY-MM-DD}"`
- `body: composed_body` (plain text)
- Do NOT set `cc` or `bcc`. Do NOT send.

Capture the returned `draft_id` and construct the review URL: `https://mail.google.com/mail/u/0/#drafts?compose={draft_id}` (Gmail's compose-from-drafts URL). If the tool returns a different URL/ID shape, use what it returns — the important thing is a link Phil can click.

**Failure handling:**
- Tool call fails → mark `email-draft-failed`, log the error, continue to step j.
- Recipient lookup returned nothing → mark `email-skipped-no-recipient` (already handled above).
- Do NOT roll back the doc prepend or tracker row. The email draft is a nice-to-have; the core capture is already committed.

**Cowork tool fallback:** If `mcp__google-workspace__draft_gmail_message` is not available in the current context, use the `gws` CLI (load `core:using-gmail` skill first for correct syntax). The draft-creation command there is equivalent.

**j. Record status** as `processed` for the summary. Also record the email outcome (`email-drafted` + draft link, `email-skipped-no-recipient`, or `email-draft-failed`) so the summary can show it.

### 6. Summary report

Print a concise summary:

```
Meeting Capture — Summary

Processed: N
Skipped (duplicate): N
Skipped (no Store ID): N
Skipped (not in Master Hub): N
Skipped (no Running Notes doc): N
Failed (doc write): N

Email drafts created: N
Email skipped (no recipient): N
Email draft failed: N

Processed mx:
- {Business Name} ({Store ID}) — {YYYY-MM-DD}
  Notes: {Running Notes URL}
  Draft: {draft review URL, or "skipped - no recipient", or "failed - {reason}"}
- ...
```

Include Store IDs, Running Notes links, and draft email links so Phil can spot-check results and send drafts with one click.

### 7. Error handling philosophy

Per Launchpad convention: graceful degradation, no retries. A single failing meeting MUST NOT block the rest of the batch. Capture the error category in the summary and move on.

---

## Tool-name reference (Cowork)

The MCP tool names above (`mcp__granola__*`, `mcp__google-workspace__*`) come from the Waypoint project's `.mcp.json` and are the preferred invocations when available. If a tool fails with "not found" in a different Cowork context, the functional equivalents are:

- Granola operations → `granola` CLI (skill: `core:using-granola`). Load the skill first to get correct syntax.
- Google Sheets reads/writes → `gws` CLI (skill: `core:using-google-sheets`).
- Google Docs batch updates and table inserts → `gws` CLI (skill: `core:using-google-docs`).
- Google Drive file export/download → `gws` CLI (skill: `core:using-google-drive`).

Do not precheck auth — the bin wrappers handle browser popups automatically. If a command stalls 10-30s and output contains `[bridge] auth`, tell Phil: "A browser window should have opened on your Mac for authentication. Please complete the sign-in there."

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
8. **Gut Check** — neutral paragraph reading between the lines for churn signs, trust issues, or red tape; acknowledge positive relationship signals before noting concerns.
9. **MSAT Prediction** — format exactly: **MSAT Prediction: X / 5 —** brief justification <= 25 words. Default to 4 / 5 unless material risk factors outweigh positives.

---

SECTION 7 INSTRUCTIONS — GROWTH ADVISORY

Growth advisory (GA) is any discussion aimed at helping the mx grow their business. This includes but is not limited to: marketplace optimization (menu edits, item photos, keywords, descriptions, pricing strategy, item availability), sponsored listings or promotional campaigns, converting marketplace volume to first-party channels (DoorDash Direct, 1P online ordering), driving additional traffic via loyalty (OCL), kiosk, gift cards, catering, group orders, or new dayparts, and expansion (new locations, markets, or channels).

There will be many calls where GA is not discussed. Handle this gracefully — do not force it.

**Step 1 — GA Topic Extraction**

If GA topics were discussed, output a markdown table with the following columns:

**Topic | Bucket | Initiated By | Commitment**

- Topic: brief description of what was discussed (one line, specific)
- Bucket: must be exactly one of — Marketplace Optimization / Promotions & Ads / 1P Conversion / Traffic Drivers / Expansion / Other
- Initiated By: AM or Mx
- Commitment: Yes / Partial / No

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
- [ ] Missed opportunity flags cite a specific signal from the mx, not a general assumption.
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
- Granola timestamps are in the meeting organizer's timezone, NOT normalized to PDT. For the date portion (YYYY-MM-DD) this rarely matters, but if a call crosses midnight in a different timezone the dedupe key could shift by a day. Cross-reference Google Calendar via `get_events` if a specific meeting's date looks off.
- Running Notes column is currently BV. The skill auto-detects by header name in case the column shifts.
- The log sheet `v2` tab drives downstream automations. Do NOT write to Sheet1 or Sheet4.
- Master Hub lives at `1ndVs2lPhS5frpkEV0KzK7ec5aS18fmr9h1BQEu099E4` (default first tab, `gid=0`). Single header row on row 1; data from row 2.
- Formatting is non-negotiable: prepends MUST use real Google Docs H1/H2 styles, real Docs tables (via `create_table_with_data`), real bullet lists, and Arial 11 body. Markdown-as-plaintext inserts (pipe tables, `#` headings, `*` bullets rendered literally) are broken output, not "good enough." Reference doc: `1odvvOQpOm_m0G7WR8hlwKTzZYxI_j74JoSA8W2d3Trs`.
- Always pass `user_google_email: "philip.bornhurst@doordash.com"` to every google-workspace MCP call. No exceptions.
