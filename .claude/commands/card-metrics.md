# /card-metrics — Pathfinder Card Volume Metrics

Show active stores, card volume, and card GOV at daily/weekly/monthly granularity with period-over-period and 7-period-ago comparisons. Excludes kiosk-only stores.

## Instructions

### Step 1: Run the Query

Execute the following SQL via `mcp__ask-data-ai__ExecuteSnowflakeQuery`:

```sql
with
  kiosk_only as (
    select
      store_id,
      store_name,
      min(submit_platform) as min_submit_platform,
      max(submit_platform) as max_submit_platform
    from
      edw.pathfinder.fact_pathfinder_orders
    where
      active_date >= '2023-01-01'
      and store_id not in (30553809)
    group by
      1,
      2
    having
      min_submit_platform = 'self_kiosk'
      and max_submit_platform = 'self_kiosk'
  ),
  base_daily as (
    select
      psd.calendar_date,
      psd.store_id,
      psd.total_card_orders as card_volume,
      psd.total_card_gov as card_gov
    from
      edw.pathfinder.agg_pathfinder_stores_daily psd
    where
      psd.calendar_date >= '2024-12-30'
      and psd.store_id not in (
        select
          store_id
        from
          kiosk_only
      )
  ),
  per_store_period as (
    select
      date_trunc('day', calendar_date) as period_date,
      'daily' as period_type,
      store_id,
      sum(card_volume) as store_card_volume,
      sum(card_gov) as store_card_gov
    from
      base_daily
    group by
      1, 2, 3
    union all
    select
      date_trunc('week', calendar_date) as period_date,
      'weekly' as period_type,
      store_id,
      sum(card_volume) as store_card_volume,
      sum(card_gov) as store_card_gov
    from
      base_daily
    group by
      1, 2, 3
    union all
    select
      date_trunc('month', calendar_date) as period_date,
      'monthly' as period_type,
      store_id,
      sum(card_volume) as store_card_volume,
      sum(card_gov) as store_card_gov
    from
      base_daily
    group by
      1, 2, 3
  ),
  aggregated_period as (
    select
      period_date,
      period_type,
      count(distinct iff(store_card_volume >= 70, store_id, null)) as n_active_stores,
      sum(store_card_volume) as card_volume,
      sum(store_card_gov) as card_gov
    from
      per_store_period
    group by
      1, 2
  )
select
  period_type,
  period_date,
  n_active_stores,
  card_volume,
  card_gov,
  lag(n_active_stores) over (
    partition by period_type order by period_date
  ) as prev_n_active_stores,
  lag(card_volume) over (
    partition by period_type order by period_date
  ) as prev_card_volume,
  lag(card_gov) over (
    partition by period_type order by period_date
  ) as prev_card_gov,
  (n_active_stores - lag(n_active_stores) over (
    partition by period_type order by period_date
  )) / nullif(lag(n_active_stores) over (
    partition by period_type order by period_date
  ), 0) as pct_change_active_stores,
  (card_volume - lag(card_volume) over (
    partition by period_type order by period_date
  )) / nullif(lag(card_volume) over (
    partition by period_type order by period_date
  ), 0) as pct_change_card_volume,
  (card_gov - lag(card_gov) over (
    partition by period_type order by period_date
  )) / nullif(lag(card_gov) over (
    partition by period_type order by period_date
  ), 0) as pct_change_card_gov,
  lag(n_active_stores, 7) over (
    partition by period_type order by period_date
  ) as prev_n_active_stores_7_period,
  lag(card_volume, 7) over (
    partition by period_type order by period_date
  ) as prev_card_volume_7_period,
  lag(card_gov, 7) over (
    partition by period_type order by period_date
  ) as prev_card_gov_7_period,
  (n_active_stores - prev_n_active_stores_7_period) / nullif(prev_n_active_stores_7_period, 0) as pct_change_active_stores_7_period,
  (card_volume - prev_card_volume_7_period) / nullif(prev_card_volume_7_period, 0) as pct_change_card_volume_7_period,
  (card_gov - prev_card_gov_7_period) / nullif(prev_card_gov_7_period, 0) as pct_change_card_gov_7_period
from
  aggregated_period
order by
  period_type,
  period_date desc
```

### Step 2: Parse and Present

**Data freshness check:** The daily row's `period_date` should be yesterday (today - 1). If it's older than yesterday, the data pipeline hasn't caught up yet. Display: **"Yesterday's data not available yet. Latest available: [actual date]."** Still show the table, but label it with the actual date — do NOT present stale data as if it's yesterday's numbers.

Split results by `period_type`. For each granularity, take the **most recent row** (first row after ordering by period_date desc) as "current" and use the lag columns for comparisons.

Format percent changes: positive = `+X.X%` (green context), negative = `-X.X%` (red context), zero/null = `—`.
Format GOV as dollars with commas (e.g., `$1,234,567`).
Format volume with commas (e.g., `12,345`).

Present in this format:

```
## Pathfinder Card Metrics — [today's date]

### Daily (latest: [period_date])
| Metric | Current | Prior Day | Δ | 7 Days Ago | Δ |
|--------|---------|-----------|---|------------|---|
| Active Stores (≥70 orders) | X | Y | +Z.Z% | A | +B.B% |
| Card Volume | X | Y | +Z.Z% | A | +B.B% |
| Card GOV | $X | $Y | +Z.Z% | $A | +B.B% |

### Weekly (latest: week of [period_date])
| Metric | Current | Prior Week | Δ | 7 Weeks Ago | Δ |
|--------|---------|------------|---|-------------|---|
| Active Stores (≥70 orders) | X | Y | +Z.Z% | A | +B.B% |
| Card Volume | X | Y | +Z.Z% | A | +B.B% |
| Card GOV | $X | $Y | +Z.Z% | $A | +B.B% |

### Monthly (latest: [month name])
| Metric | Current | Prior Month | Δ | 7 Months Ago | Δ |
|--------|---------|-------------|---|--------------|---|
| Active Stores (≥70 orders) | X | Y | +Z.Z% | A | +B.B% |
| Card Volume | X | Y | +Z.Z% | A | +B.B% |
| Card GOV | $X | $Y | +Z.Z% | $A | +B.B% |

### Notable Movements
- Flag any metric with >10% period-over-period swing
- Flag any metric with >15% 7-period swing
- Note if active store count is declining while volume holds (concentration risk)
- Note if GOV is dropping faster than volume (ticket size compression)
```

### Step 3: Trend Context (if requested)

If the user asks for more detail, show the last 4 rows for each period type as a trend table:

```
### Daily Trend (last 4 days)
| Date | Active Stores | Card Volume | Card GOV |
|------|---------------|-------------|----------|
| ... | ... | ... | ... |
```

## Example usage

```
/card-metrics                ← latest snapshot (default)
/card-metrics show trends    ← include 4-period trend tables
/card-metrics weekly only    ← only show weekly granularity
```
