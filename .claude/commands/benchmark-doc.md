# /benchmark-doc — Marketplace Benchmarking Doc Generator

Turn a DoorDash competitive-benchmarking xlsx into a merchant-facing Google Doc that surfaces the most material insights up front, includes the supporting detail, and ends with actionable recommendations. Outputs land in `2026/benchmarking/` (folder created if missing) and a summary posts to `#phils-gumloop-agent`.

## Usage

```
/benchmark-doc M Spoon 35534521
/benchmark-doc M Spoon 35534521 "/Users/philip.bornhurst/Downloads/Combined Version.xlsx"
/benchmark-doc Sarpino's Pizza 12345 "/path/to/other-file.xlsx"
```

**Arguments (parsed from `$ARGUMENTS`):**
- Last numeric token → `store_id`
- Last quoted token or `.xlsx`-ending token → `xlsx_path` (defaults to `/Users/philip.bornhurst/Downloads/Combined Version.xlsx`)
- Everything else → `business_name`

## Instructions

1. Parse `$ARGUMENTS` per the rules above. If `business_name` or `store_id` is missing, ask Phil for it and stop.
2. Dispatch the `benchmark-doc` agent with the parsed arguments. The agent handles parsing the xlsx, synthesizing the scorecard + insights + recommendations, creating the styled Google Doc, sharing it to doordash.com, and posting the Slack summary.
3. Return the doc URL and the top 3 insights inline.

## What lands in the doc

1. **Big Scorecard table** (front and center): You vs Category Avg vs Top 5 Peers Avg vs Delta, with green/amber/red status per metric.
2. **Top 3 Insights** — bordered callouts with specific numbers.
3. **Recommendations** — 3 verb-led actions, each tied to a workbook data point.
4. **Watch-outs** — 1–3 amber callouts.
5. **Supporting Detail** — Sales & Rank · Visibility & Traffic Sources · Search Demand · Customer Mix · Operational Quality · Competitive Landscape · Geographic Reach.

## Pageless layout

Google Docs' "pageless" mode is UI-only; the public API doesn't expose a toggle. The doc is created in pages mode — Phil flips it to pageless in one click via **File → Page setup → Pageless**. The agent's Slack message includes this reminder.
