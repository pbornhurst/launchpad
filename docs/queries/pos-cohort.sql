-- POS Cohort Query (per-mx)
-- Canonical query for per-mx lifecycle and performance data.
-- Returns the entire POS cohort (live and churned) with lifecycle dates,
-- segments, and key weekly metrics.
--
-- Filter `WHERE pf.store_id = [STORE_ID]` in the final SELECT (or wrap as CTE)
-- to scope to a single mx.
--
-- Key per-mx metrics:
--   Lifetime OSW (Orders per Store Week)  = 7 * (lifetime_card_orders / total_active_days)
--   Lifetime GOV Store Week               = 7 * (lifetime_card_gov / total_active_days)
--   AOV                                   = lifetime_card_gov / lifetime_card_orders
--   Go-active date                        = first date where trailing 7d card orders >= 70
--   Sustained activation                  = >=70 orders/week maintained 7+ days after go-active

with
  kiosk_only as (
    select store_id,
      min(submit_platform) as min_submit_platform,
      max(submit_platform) as max_submit_platform
    from edw.pathfinder.fact_pathfinder_orders
    where active_date >= '2023-01-01' and store_id not in (30553809)
    group by all
    having min_submit_platform = 'self_kiosk' and max_submit_platform = 'self_kiosk'
  ),
  store_dates as (
    select store_id, cw_date, OB_CALL_DATE_CLEANED as ob_date
    from proddb.public.pathfinder_merchant_database_from_gsheet_cleaned
    qualify row_number() over (partition by store_id order by cw_date desc) = 1
  ),
  pf as (
    select
      psd.store_id,
      psd.live_date as install_date,
      sd.cw_date,
      sd.ob_date,
      datediff('days', try_to_date(sd.cw_date), try_to_date(sd.ob_date)) as cs_to_ob_days,
      datediff('days', try_to_date(sd.ob_date), try_to_date(psd.live_date)) as ob_to_install_days,
      min(iff(psd.total_card_orders_l7d >= 70, psd.calendar_date, null)) as go_active_date,
      max(iff(psd.total_card_orders > 0, psd.calendar_date, null)) as last_card_order_date,
      datediff('day', go_active_date, last_card_order_date) + 1 as total_active_days,
      sum(psd.total_card_orders) as lifetime_card_orders,
      sum(psd.total_card_gov) as lifetime_card_gov,
      lifetime_card_gov / nullif(lifetime_card_orders, 0) as aov,
      7 * (sum(psd.total_card_orders) / nullif(total_active_days, 0)) as lifetime_osw,
      7 * (sum(psd.total_card_gov) / nullif(total_active_days, 0)) as lifetime_gov_store_week
    from edw.pathfinder.agg_pathfinder_stores_daily psd
      left join store_dates sd on psd.store_id::varchar = sd.store_id::varchar
    where psd.store_id not in (select distinct store_id from kiosk_only)
    group by all
  ),
  sustained as (
    select d.store_id,
      d.calendar_date as first_sustained_date,
      d.total_card_orders_l7d
    from edw.pathfinder.agg_pathfinder_stores_daily d
      join pf on d.store_id = pf.store_id
    where d.calendar_date >= dateadd(day, 7, pf.go_active_date)
      and d.total_card_orders_l7d >= 70
    qualify row_number() over (partition by d.store_id order by d.calendar_date) = 1
  )
select
  ds.name as store_name,
  ds.cuisine_type,
  pf.*,
  db.management_type_grouped,
  db.management_type,
  s.total_card_orders_l7d as osw_after_go_active,
  s.first_sustained_date::date as date_sustained_activation,
  iff(s.first_sustained_date is not null, 'yes', 'no') as met_activation_threshold,
  case
    when s.first_sustained_date is null then null
    when datediff('days', pf.go_active_date, s.first_sustained_date) = 7 then 'yes'
    else 'no'
  end as met_activation_threshold_first_7d
from pf
  join edw.merchant.dimension_store ds on pf.store_id = ds.store_id
  join edw.merchant.dimension_business db on ds.business_id = db.business_id
  left join sustained s on pf.store_id = s.store_id
order by 1
