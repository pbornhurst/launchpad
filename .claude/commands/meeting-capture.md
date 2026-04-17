# /meeting-capture — Capture Granola mx Calls to Running Notes

Scan recent Granola meetings for mx calls, generate structured PRISM-TnA notes from the transcript, prepend them to the mx's Running Notes doc, and log the call to the Running Notes Input Tracker.

**Fully automated** — no confirmation gates. Commits everything, then reports a summary. Scans in tiered time windows (2h → 12h → 24h → 48h → 7d) and stops the moment it hits an mx call that's already in the tracker. Re-running back-to-back is cheap (usually bails after Tier 1).

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
- Process each meeting in newest-first order (see Step 2 for marker detection and Step 4 for per-meeting processing).
- **Stop-the-world trigger:** The moment you encounter an `mx call` meeting whose `(store_id, meeting_date)` is already in the tracker dedupe set (Section 3), halt all further tier expansion. Everything older is presumed already processed. Print the stop point in the summary.
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

**Master Hub — correct spreadsheet.** The real Master Hub is `1InzoCJDsjzyejfASR19Bvb0Q9TdtJsSNhUZjS9a7VhE`, titled "[Pathfinder] Merchant List / Launch Hub". The data tab is `Merchant Database` (NOT the default first tab "Launch Calendar"). Column headers live on **row 2** (row 1 is section group labels like "INPUT DRI: SALES"). Data starts on row 3.

> Note: CLAUDE.md currently lists a stale Master Hub ID (`1ndVs...`). The memory index at `memory/master_hub_id.md` has the correct reference — trust that until CLAUDE.md is corrected.

**Master Hub header confirmation** (future-proof against column shifts):

- `mcp__google-workspace__read_sheet_values`
  - `spreadsheet_id: "1InzoCJDsjzyejfASR19Bvb0Q9TdtJsSNhUZjS9a7VhE"`
  - `range_name: "Merchant Database!A2:CA2"`
  - `user_google_email: "philip.bornhurst@doordash.com"`
- Locate the column index where header equals exactly `"Running Notes"`. Expected: column BV (index 73). If it has moved, use the discovered column.

**Master Hub body.** The `read_sheet_values` tool display-truncates at ~50 rows even on successful larger reads, which makes per-row lookups flaky. Instead:

- Call `mcp__google-workspace__get_drive_file_download_url` with `file_id: "1InzoCJDsjzyejfASR19Bvb0Q9TdtJsSNhUZjS9a7VhE"` and `export_format: "xlsx"`.
- Parse the downloaded `.xlsx` with Python + `openpyxl` (install via `pip3 install openpyxl` if needed). Target sheet: `Merchant Database`. Headers on row 2, data from row 3.
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

### 4. Per-meeting loop (sequential, not parallel)

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

**h. Prepend to the Running Notes doc using real Google Docs formatting** — NOT plaintext markdown.

The reference for target format is doc ID `1odvvOQpOm_m0G7WR8hlwKTzZYxI_j74JoSA8W2d3Trs`. It uses real H1/H2 styles, real Docs tables with header rows, real bulleted lists, and Arial body. Raw markdown pipes and `#` symbols are NOT acceptable — they render as literal text and look terrible.

Execute the following phases in order. Between phases, re-call `inspect_doc_structure` with `detailed=true` to get fresh indices.

**Phase 1 — Insert text skeleton with paragraph styles (single `batch_update_doc` call).**

Build an ops list that inserts all heading and narrative text at incrementing indices starting at `cursor = 1`. For each block, `insert_text` with `text = content + "\n"`, then apply the paragraph style with `update_paragraph_style` over `[cursor, cursor + len(text)]`, then advance `cursor += len(text)`.

Insert, in this order, with these styles (all text lines terminated with `\n`):

1. `"{title}\n"` → `HEADING_1`
2. `"Metadata\n"` → `HEADING_2`
3. `"\n"` → `NORMAL_TEXT` (placeholder paragraph — Phase 2 will insert the metadata table here)
4. `"Detailed Bullet Notes\n"` → `HEADING_2`
5. For each bullet: `"{bullet_text}\n"` → `NORMAL_TEXT` (we'll convert to real bullets in Phase 3)
6. `"Action Items\n"` → `HEADING_2`
7. `"\n"` → placeholder for action_items table
8. `"Feature Requests, Gaps & Product Feedback\n"` → `HEADING_2`
9. `"\n"` → placeholder for feature_requests table
10. `"Tone & Character\n"` → `HEADING_2`
11. `"\n"` → placeholder for tone table
12. `"Insights or Flags\n"` → `HEADING_2`
13. `"{insights_text}\n"` → `NORMAL_TEXT`
14. `"Growth Advisory\n"` → `HEADING_2`
15. If `has_topics`: `"\n"` placeholder for topics table, `"\n"` missed opportunity paragraph (if any), `"\n"` placeholder for score table, `"{composite_line}\n"`. Else if `missed_opportunity` only: missed opportunity paragraph + `"\n"` placeholder for score table + composite line. Else: a single paragraph `"No growth advisory topics were discussed in this call. No missed opportunities identified. Score: N/A\n"`.
16. `"Gut Check\n"` → `HEADING_2`
17. `"{gut_check_text}\n"` → `NORMAL_TEXT`
18. `"MSAT Prediction\n"` → `HEADING_2`
19. `"{msat_line}\n"` → `NORMAL_TEXT`
20. `"===\n"` → `NORMAL_TEXT`
21. `"\n"` → `NORMAL_TEXT` (trailing breathing room above the existing doc body)

**Phase 2 — Insert real Docs tables at every placeholder (BOTTOM-UP).**

Call `inspect_doc_structure` with `detailed=true` on the target doc. Identify each placeholder paragraph by its position (the blank `\n` lines immediately after each table-owning H2 heading, plus the GA topics/score placeholders inside the Growth Advisory block). Record their `start_index` values.

Process tables from BOTTOM (highest `start_index`) to TOP (lowest). For each table, call `mcp__google-workspace__create_table_with_data`:

- `document_id: "{doc_id}"`
- `user_google_email: "philip.bornhurst@doordash.com"`
- `index: {placeholder.start_index}`
- `bold_headers: true`
- `table_data: {2D array, first row = header}`

Processing bottom-up means earlier placeholders' indices remain valid as we insert. If you mix things up, re-call `inspect_doc_structure` between tables rather than guessing.

Tables to insert:
- Metadata table — 4 rows × 2 cols, no bold header (or `bold_headers: false` since this is key-value, not tabular). Use `bold_headers: false` for Metadata specifically; `true` for all others.
- Action Items — header row + N rows × 3 cols
- Feature Requests — header row + N rows × 3 cols
- Tone & Character — header row + N rows × 3 cols
- GA Topics (if present) — header row + N rows × 4 cols
- GA Score (if present) — header row + N rows × 3 cols

**Phase 3 — Convert bullet lines into real Docs bullets (single `batch_update_doc` call).**

Re-call `inspect_doc_structure` with `detailed=true`. Locate the range covering the Detailed Bullet Notes body (all paragraphs between the "Detailed Bullet Notes" heading and the "Action Items" heading). Apply `create_bullet_list` over that range:

```
{
  "type": "create_bullet_list",
  "start_index": {first_bullet.start_index},
  "end_index": {last_bullet.end_index},
  "list_type": "UNORDERED"
}
```

**Phase 4 — Body font (single `batch_update_doc` call).**

Apply `format_text` with `font_family: "Arial"` and `font_size: 11` across the entire prepended block (from `start_index = 1` to the end of the trailing blank line). Heading styles already carry their own font settings; this step ensures body text and table cells render in Arial 11 to match Launchpad doc conventions. Do NOT override heading colors or sizes — let named styles win.

**If ANY phase fails** (permissions, doc deleted, schema error), mark the meeting `failed-doc-write`, log the phase that failed, and continue to the next meeting without rollback. Partial prepends are acceptable — Phil can clean them up manually, whereas failing the whole batch loses the rest of the captures.

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

**j. Record status** as `processed` for the summary.

### 5. Summary report

Print a concise summary:

```
Meeting Capture — Summary

Processed: N
Skipped (duplicate): N
Skipped (no Store ID): N
Skipped (not in Master Hub): N
Skipped (no Running Notes doc): N
Failed (doc write): N

Processed mx:
- {Business Name} ({Store ID}) — {YYYY-MM-DD} — {Running Notes URL}
- ...
```

Include Store IDs and Running Notes links so Phil can spot-check results immediately.

### 6. Error handling philosophy

Per Launchpad convention: graceful degradation, no retries. A single failing meeting MUST NOT block the rest of the batch. Capture the error category in the summary and move on.

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
```

## Notes

- The command relies on Phil adding an `mx call` marker and a Store ID to the top of each Granola meeting's private notes. Without the marker the meeting is ignored.
- Granola timestamps are in the meeting organizer's timezone, NOT normalized to PDT. For the date portion (YYYY-MM-DD) this rarely matters, but if a call crosses midnight in a different timezone the dedupe key could shift by a day. Cross-reference Google Calendar via `get_events` if a specific meeting's date looks off.
- Running Notes column is currently BV. The command auto-detects by header name in case the column shifts.
- The log sheet `v2` tab drives downstream automations. Do NOT write to Sheet1 or Sheet4.
- Master Hub lives at `1InzoCJDsjzyejfASR19Bvb0Q9TdtJsSNhUZjS9a7VhE`, tab `Merchant Database`, headers on row 2. Ignore CLAUDE.md's stale ID until it's corrected there.
- Formatting is non-negotiable: prepends MUST use real Google Docs H1/H2 styles, real Docs tables (via `create_table_with_data`), real bullet lists, and Arial 11 body. Markdown-as-plaintext inserts (pipe tables, `#` headings, `*` bullets rendered literally) are broken output, not "good enough." Reference doc: `1odvvOQpOm_m0G7WR8hlwKTzZYxI_j74JoSA8W2d3Trs`.
