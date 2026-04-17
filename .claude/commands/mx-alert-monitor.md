# /mx-alert-monitor — Merchant Alert Monitor

Intraday anomaly check using **real-time** Snowflake data. Detects POS-dark stores, channel-specific volume drops, and possible churn signals. Posts to Slack ONLY when action needed. Designed for both manual and headless (launchd) execution.

> **Volume only** — no Intercom checks. Keeps the monitor fast and reliable. Support is covered by `/daily-brief` and `/support-scan`.

## Instructions

### Step 1: Read Master Hub (Live Stores Only)

Use `mcp__google-workspace__read_sheet_values`:
- `spreadsheet_id: "1ndVs2lPhS5frpkEV0KzK7ec5aS18fmr9h1BQEu099E4"`
- `user_google_email: "philip.bornhurst@doordash.com"`
- Read columns A through I (Status, Business Name, Location, Business ID, Store ID, Mx Tier, Account Health, Mx File, Account Manager)
- Read ALL rows (the sheet may require multiple reads if truncated — read in chunks until you have all rows)

**Extract only rows where Status = "Live" (exact match).** Build a lookup of Live stores:
- Store ID → Business Name, Tier, Account Manager

Collect all numeric Store IDs from the Live rows. Skip any rows where Store ID is blank, "TBD", "Net New", or non-numeric.

### Step 2: Query Intraday Volume (Snowflake)

Run **three separate queries** via Bash: `python3 scripts/snowflake_query.py --json "SQL_HERE"` (direct Snowflake connection, no OAuth needed) — one per alert type. Run all three in parallel.

**CRITICAL — Data source:** Uses `order_data.public.flink_ingest_store_order_cart` — a Flink CDC streaming table with ~15 minute latency. This is the fastest available source. Do NOT use `proddb.public.maindb_store_order_cart` (~5 hour replication lag) or `edw.merchant.fact_merchant_sales` (T+1 ETL lag). This table captures ALL POS transactions (card + cash).

**CRITICAL — Timezone handling:** The Snowflake session runs in UTC. The `created_at` column in `flink_ingest_store_order_cart` is in UTC. You MUST use `CONVERT_TIMEZONE('UTC', 'America/Los_Angeles', ...)` to convert both `CURRENT_TIMESTAMP()` and `created_at` to PST for proper date/time window comparisons.

**CRITICAL — Channel mapping:** The `tenant_id` column distinguishes order channels:
- **POS/In-store:** `tenant_id IN ('dd_pos', 'self_kiosk')`
- **Marketplace:** `tenant_id = 'doordash'`
- **Storefront:** `tenant_id LIKE 'storefront:%'` (not used in alerts, but FYI)

**CRITICAL — Store scope:** The WHERE clause must filter to ONLY the Live store IDs from Step 1. Use `soc.store_id IN (id1, id2, id3, ...)` with the full list of Live store IDs. Do NOT use the `edw.pathfinder.agg_pathfinder_stores_daily` table — it misses stores without recent card orders (e.g., cash-heavy or newly live stores).

All three queries share this common CTE structure:

```sql
WITH time_params AS (
  SELECT
    CONVERT_TIMEZONE('UTC', 'America/Los_Angeles', CURRENT_TIMESTAMP())::DATE AS today_pst,
    CONVERT_TIMEZONE('UTC', 'America/Los_Angeles', CURRENT_TIMESTAMP())::TIME AS now_time_pst
),
volume AS (
  SELECT
    soc.store_id,
    SUM(CASE WHEN CONVERT_TIMEZONE('UTC', 'America/Los_Angeles', soc.created_at)::DATE = tp.today_pst
              AND CONVERT_TIMEZONE('UTC', 'America/Los_Angeles', soc.created_at)::TIME <= tp.now_time_pst
              AND soc.tenant_id IN ('dd_pos', 'self_kiosk') THEN 1 ELSE 0 END) AS pos_today,
    SUM(CASE WHEN CONVERT_TIMEZONE('UTC', 'America/Los_Angeles', soc.created_at)::DATE = tp.today_pst
              AND CONVERT_TIMEZONE('UTC', 'America/Los_Angeles', soc.created_at)::TIME <= tp.now_time_pst
              AND soc.tenant_id = 'doordash' THEN 1 ELSE 0 END) AS mx_today,
    SUM(CASE WHEN CONVERT_TIMEZONE('UTC', 'America/Los_Angeles', soc.created_at)::DATE = DATEADD('day', -7, tp.today_pst)
              AND CONVERT_TIMEZONE('UTC', 'America/Los_Angeles', soc.created_at)::TIME <= tp.now_time_pst
              AND soc.tenant_id IN ('dd_pos', 'self_kiosk') THEN 1 ELSE 0 END) AS pos_lw,
    SUM(CASE WHEN CONVERT_TIMEZONE('UTC', 'America/Los_Angeles', soc.created_at)::DATE = DATEADD('day', -7, tp.today_pst)
              AND CONVERT_TIMEZONE('UTC', 'America/Los_Angeles', soc.created_at)::TIME <= tp.now_time_pst
              AND soc.tenant_id = 'doordash' THEN 1 ELSE 0 END) AS mx_lw
  FROM order_data.public.flink_ingest_store_order_cart soc
  CROSS JOIN time_params tp
  WHERE soc.store_id IN (/* comma-separated Live store IDs from Step 1 */)
    AND soc.created_at >= DATEADD('day', -8, CURRENT_TIMESTAMP())
    AND soc.created_at <= CURRENT_TIMESTAMP()
    AND soc.cancelled_at IS NULL
  GROUP BY soc.store_id
)
```

**Query 1 — POS_DARK_MX_ACTIVE:**
```sql
-- append after the common CTEs above:
SELECT store_id, pos_today, mx_today, pos_lw, mx_lw, 'POS_DARK_MX_ACTIVE' AS alert_type,
       TO_CHAR(CONVERT_TIMEZONE('UTC', 'America/Los_Angeles', CURRENT_TIMESTAMP()), 'HH12:MI AM') AS current_pst_time,
       TO_CHAR(CONVERT_TIMEZONE('UTC', 'America/Los_Angeles', CURRENT_TIMESTAMP()), 'YYYY-MM-DD') AS current_pst_date
FROM volume
WHERE pos_today = 0 AND mx_today > 0
ORDER BY mx_today DESC
LIMIT 30
```

**CRITICAL — Time display:** Query 1 includes `current_pst_time` and `current_pst_date` columns derived from Snowflake's `CURRENT_TIMESTAMP()` converted to PST. Use these values for the Slack alert header (e.g., "Mx Alert — 9:50 PM PST"). Do NOT guess the time or use the system clock — only use the Snowflake-returned PST time. If Query 1 returns 0 rows, get the time from Query 2 or 3 instead (add the same columns to whichever query returns results).

**Query 2 — BOTH_DARK:**
```sql
SELECT store_id, pos_today, mx_today, pos_lw, mx_lw, 'BOTH_DARK' AS alert_type
FROM volume
WHERE pos_today = 0 AND mx_today = 0 AND (pos_lw > 0 OR mx_lw > 0)
ORDER BY pos_lw DESC
LIMIT 20
```

**Query 3 — POS_SEVERE_DROP:**
```sql
SELECT store_id, pos_today, mx_today, pos_lw, mx_lw, 'POS_SEVERE_DROP' AS alert_type
FROM volume
WHERE pos_today > 0 AND pos_lw > 5 AND pos_today < pos_lw * 0.6
ORDER BY pos_lw DESC
LIMIT 30
```

**If the Snowflake query fails**, log "Snowflake query failed" and exit. Do NOT fall back to Volume Drop Data. Do NOT post to Slack.

**If all three queries return 0 rows:**
- Query Snowflake for current PST time: `SELECT TO_CHAR(CONVERT_TIMEZONE('UTC', 'America/Los_Angeles', CURRENT_TIMESTAMP()), 'HH12:MI AM') AS t, TO_CHAR(CONVERT_TIMEZONE('UTC', 'America/Los_Angeles', CURRENT_TIMESTAMP()), 'YYYY-MM-DD') AS d`
- Log: "No anomalies detected at [t] PST on [d]. No Slack post needed."
- Post an "all clear" to Slack (same channel, `C0AC2NK50QN`):
```
:white_check_mark: *Mx Alert — [t] PST* — All clear. [N] live stores checked, no anomalies detected.
```
  Where [N] is the count of Live store IDs from Step 1.
- EXIT

### Step 3: Classify and Post Slack Alert

Group anomalies into three categories based on `alert_type`. Use the Master Hub lookup from Step 1 to enrich each store with Business Name, Tier, and Account Manager.

**Category 1 — POS_DARK_MX_ACTIVE (HIGH alarm):**
Store is open and transacting on Marketplace but has zero POS orders. This is the strongest churn signal — the mx may have stopped using the POS.

**Category 2 — BOTH_DARK (MEDIUM alarm):**
Both POS and Marketplace are at zero today, but had activity last week. Likely a temporary closure (holiday, renovation, etc.) but still worth watching.

**Category 3 — POS_SEVERE_DROP (YELLOW):**
POS orders are down >40% compared to the same time window last week. Store is still transacting but volume is significantly lower. Only flags stores with >5 POS orders last week to avoid noise.

Use `mcp__slack__slack_send_message`:
- `channel_id: "C0AC2NK50QN"` (#phils-gumloop-agent)
- **Always post directly — NEVER ask for confirmation before sending.** This command is designed for headless/automated execution.

**Format:**

```
*Mx Alert — [time PST]*

[If POS_DARK_MX_ACTIVE stores exist:]
:red_circle: *POS Down / Store Open (Possible Churn):*
- *[mx name]* (Store [ID], [tier]) — POS: [N]→0, Marketplace: [M] active | <https://www.doordash.com/merchant/sales?store_id=[ID]|Portal>

[If BOTH_DARK stores exist:]
:large_yellow_circle: *Both Channels Dark:*
- *[mx name]* (Store [ID], [tier]) — was [N] POS + [M] Mx orders last week, now 0 | <https://www.doordash.com/merchant/sales?store_id=[ID]|Portal>

[If POS_SEVERE_DROP stores exist:]
:warning: *POS Severe Drop (>40%):*
- *[mx name]* (Store [ID], [tier]) — POS: [prev]→[curr] (-XX%) | <https://www.doordash.com/merchant/sales?store_id=[ID]|Portal>

_Comparing today so far vs same time window last week. Run `/churn-risk` for full health score analysis._
```

**Prioritize ICP and Tier 1 mx at the top of each category.**

## Key Design Notes

- **Master Hub is the source of truth for store scope.** Only stores with Status = "Live" in the Master Hub are monitored. This replaced the old approach of using `edw.pathfinder.agg_pathfinder_stores_daily` which missed stores without recent card orders (e.g., cash-heavy, newly live, or stores like Great Khan's that only had marketplace activity).
- **Real-time data source:** `order_data.public.flink_ingest_store_order_cart` is a Flink CDC streaming table with ~15 minute latency. This replaced `proddb.public.maindb_store_order_cart` (~5 hour replication lag) which itself replaced `edw.merchant.fact_merchant_sales` (T+1 ETL lag). The Flink table captures ALL POS transactions including cash orders — counts will match the merchant portal exactly.
- **Timezone-critical:** The Snowflake session runs in UTC. `created_at` in the Flink table is in UTC. You MUST use `CONVERT_TIMEZONE('UTC', 'America/Los_Angeles', ...)` to derive PST dates and times for both the current timestamp and order timestamps.
- **Broad WHERE, precise CASE:** The WHERE clause uses a broad UTC time range (`DATEADD('day', -8, ...)`) for efficient partition pruning. The CASE statements handle precise PST date/time matching.
- **Cancelled order filtering:** `cancelled_at IS NULL` excludes cancelled orders. This is critical — without it, cancelled orders inflate counts.
- **Same day-of-week comparison:** The query compares today (e.g., Tuesday) to last week's same day (last Tuesday), using the exact same time window (midnight to current PST time). This avoids false signals from stores that open late or have different weekend patterns.
- **Three separate queries:** Split by alert type to stay under MCP result payload limits. Run all three in parallel.
- **Minimum threshold (POS_SEVERE_DROP only):** Requires last week POS > 5 orders. This avoids noise from barely-active stores. POS_DARK_MX_ACTIVE and BOTH_DARK have no minimum — any Live store going dark matters.
- **Channel distinction is the key insight:** POS dark + Marketplace active = store is OPEN but not using POS = strongest churn signal. Both dark = likely just closed temporarily.
- **No retries, no fallbacks.** If Snowflake fails, exit silently. The next scheduled run (every ~4 hours) will catch it.

## Example usage

```
/mx-alert-monitor
```
