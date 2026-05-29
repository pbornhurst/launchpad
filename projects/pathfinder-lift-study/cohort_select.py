#!/usr/bin/env python3
"""
Pathfinder Lift Study — Phase 1: cohort selection.

Picks 10 mx that meet the study criteria (Pathfinder live >= 6M, lifetime
in-store OSW >= 300), diversified across cuisine bucket, region, and
management type. Writes data/cohort.json.

Usage:
  python3 cohort_select.py
  python3 cohort_select.py --exclude STORE_ID [STORE_ID ...]
  python3 cohort_select.py --target N        # default 10
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SNOW = REPO_ROOT / "scripts" / "snowflake_query.py"
DATA_DIR = Path(__file__).resolve().parent / "data"


COHORT_SQL = """
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
  )
select
  pf.store_id,
  ds.name as store_name,
  ds.cuisine_type,
  ds.submarket_name,
  ds.market_name,
  ds.region_name,
  ds.country_shortname,
  db.management_type_grouped,
  db.management_type,
  pf.install_date::date as install_date,
  pf.go_active_date::date as go_active_date,
  pf.last_card_order_date::date as last_card_order_date,
  pf.total_active_days,
  pf.lifetime_card_orders,
  pf.lifetime_card_gov,
  pf.aov,
  pf.lifetime_osw,
  pf.lifetime_gov_store_week
from pf
  join edw.merchant.dimension_store ds on pf.store_id = ds.store_id
  join edw.merchant.dimension_business db on ds.business_id = db.business_id
where pf.total_active_days >= 180
  and pf.lifetime_osw >= 300
  and pf.install_date is not null
  and pf.install_date <= dateadd(month, -6, current_date)
  and ds.country_shortname = 'US'
order by pf.lifetime_osw desc
limit 500
"""


# Cuisine bucketing for diversity scoring. Match against the FIRST
# comma-separated cuisine token (the primary cuisine). Order in the dict
# matters: most-specific buckets must come before broader ones.
CUISINE_BUCKETS = {
    "Pizza": ["pizza"],
    "Mexican": ["mexican", "latin", "tex-mex", "taco"],
    "Asian": ["chinese", "japanese", "thai", "vietnamese", "korean", "sushi", "asian", "ramen", "poke", "filipino", "indian", "hawaiian"],
    "Chicken/Wings": ["chicken", "wing"],
    "Burgers": ["burger"],
    "Sandwiches": ["sandwich", "sub", "deli"],
    "Italian": ["italian"],
    "Mediterranean": ["mediterranean", "middle eastern", "greek", "lebanese", "halal"],
    "Healthy": ["salad", "healthy", "vegetarian", "vegan", "acai", "juice"],
    "Cafe/Bakery": ["cafe", "coffee", "bakery", "breakfast", "brunch", "dessert", "ice cream", "boba", "donut", "doughnut"],
    "Seafood": ["seafood"],
    "BBQ": ["bbq", "barbecue"],
    "American": ["american", "diner", "comfort"],
}

# Map DoorDash region_name values to coarse US macro-regions.
REGION_BUCKETS = {
    "West": ["northern california", "southern california", "mountain", "pacific northwest"],
    "Northeast": ["new york", "northeast"],
    "Midwest": ["midwest"],
    "South": ["southeast", "texas", "florida", "south"],
}


def bucket_cuisine(cuisine):
    if not cuisine:
        return "Other"
    primary = cuisine.split(",")[0].strip().lower()
    for bucket, needles in CUISINE_BUCKETS.items():
        for needle in needles:
            if needle in primary:
                return bucket
    return "Other"


def bucket_region(submarket, region_name, market):
    region = (region_name or "").strip().lower()
    for bucket, needles in REGION_BUCKETS.items():
        for needle in needles:
            if needle in region:
                return bucket
    # Fall back to submarket if region_name is unrecognized.
    sub = (submarket or "").strip().lower()
    for bucket, needles in REGION_BUCKETS.items():
        for needle in needles:
            if needle in sub:
                return bucket
    return "Other"


def bucket_mgmt(mgmt):
    # DoorDash uses MANAGED SMB vs UNMANAGED SMB as the primary split.
    if not mgmt:
        return "Unknown"
    return mgmt.strip().title()


def run_snowflake(sql: str) -> list[dict]:
    """Run a SQL query via snowflake_query.py and parse JSON output."""
    result = subprocess.run(
        ["python3", str(SNOW), "--json", sql],
        capture_output=True,
        text=True,
        timeout=180,
    )
    if result.returncode != 0:
        sys.stderr.write(result.stderr)
        raise RuntimeError(f"Snowflake query failed (exit {result.returncode})")
    return json.loads(result.stdout)


def add_diversity_buckets(rows: list[dict]) -> list[dict]:
    for r in rows:
        r["cuisine_bucket"] = bucket_cuisine(r.get("CUISINE_TYPE"))
        r["region_bucket"] = bucket_region(
            r.get("SUBMARKET_NAME"), r.get("REGION_NAME"), r.get("MARKET_NAME")
        )
        r["mgmt_bucket"] = bucket_mgmt(r.get("MANAGEMENT_TYPE_GROUPED"))
    return rows


def pick_diversified(rows, target, exclude):
    """
    Greedy diversification with a per-region cap to prevent the cohort from
    skewing to one region (the eligible pool is heavily West).

      Pass 1 — fresh (cuisine, region, mgmt) triple AND region count < cap.
      Pass 2 — fresh cuisine AND region count < cap (relax mgmt).
      Pass 3 — region count < cap (just keep regional balance).
      Pass 4 — fill remaining from top of list (no caps).
    """
    eligible = [r for r in rows if str(r["STORE_ID"]) not in exclude]
    eligible.sort(key=lambda r: float(r["LIFETIME_OSW"] or 0), reverse=True)

    # Cap = ceil(target / observed-region-count), max 3 per region so
    # we hit at least 4 regions in a target=10 cohort.
    observed_regions = {r["region_bucket"] for r in eligible}
    region_cap = max(2, min(3, (target + len(observed_regions) - 1) // max(1, len(observed_regions))))

    picked = []
    seen_triples = set()
    seen_cuisines = set()
    region_counts = defaultdict(int)
    picked_ids = set()

    def add(r, reason):
        r = dict(r)
        r["selection_reason"] = reason
        picked.append(r)
        picked_ids.add(str(r["STORE_ID"]))
        seen_triples.add((r["cuisine_bucket"], r["region_bucket"], r["mgmt_bucket"]))
        seen_cuisines.add(r["cuisine_bucket"])
        region_counts[r["region_bucket"]] += 1

    for r in eligible:
        if len(picked) >= target:
            break
        if str(r["STORE_ID"]) in picked_ids:
            continue
        triple = (r["cuisine_bucket"], r["region_bucket"], r["mgmt_bucket"])
        if triple not in seen_triples and region_counts[r["region_bucket"]] < region_cap:
            add(r, "pass1_unique_triple_capped")

    for r in eligible:
        if len(picked) >= target:
            break
        if str(r["STORE_ID"]) in picked_ids:
            continue
        if r["cuisine_bucket"] not in seen_cuisines and region_counts[r["region_bucket"]] < region_cap:
            add(r, "pass2_fresh_cuisine_capped")

    for r in eligible:
        if len(picked) >= target:
            break
        if str(r["STORE_ID"]) in picked_ids:
            continue
        if region_counts[r["region_bucket"]] < region_cap:
            add(r, "pass3_region_capped")

    for r in eligible:
        if len(picked) >= target:
            break
        if str(r["STORE_ID"]) in picked_ids:
            continue
        add(r, "pass4_fill")

    return picked


def compute_windows(install_date_str: str, last_order_date_str: str) -> dict:
    install = date.fromisoformat(install_date_str)
    last = date.fromisoformat(last_order_date_str) if last_order_date_str else date.today()
    today = date.today()

    pre_start = install - timedelta(days=180)
    pre_end = install - timedelta(days=1)
    post_start = install
    post_end = install + timedelta(days=180)

    m1_3_start = install
    m1_3_end = install + timedelta(days=90) - timedelta(days=1)
    m4_6_start = install + timedelta(days=90)
    m4_6_end = install + timedelta(days=180) - timedelta(days=1)

    # Latest 3M only if mx has > 9M of tenure since install
    has_latest = (today - install).days >= 270
    latest_3m_end = today - timedelta(days=1)
    latest_3m_start = today - timedelta(days=90)

    return {
        "pre_start": pre_start.isoformat(),
        "pre_end": pre_end.isoformat(),
        "post_start": post_start.isoformat(),
        "post_end": post_end.isoformat(),
        "m1_3_start": m1_3_start.isoformat(),
        "m1_3_end": m1_3_end.isoformat(),
        "m4_6_start": m4_6_start.isoformat(),
        "m4_6_end": m4_6_end.isoformat(),
        "latest_3m_start": latest_3m_start.isoformat() if has_latest else None,
        "latest_3m_end": latest_3m_end.isoformat() if has_latest else None,
        "tenure_days_since_install": (today - install).days,
    }


def print_table(picked: list[dict]):
    cols = [
        ("#", 3),
        ("Store ID", 10),
        ("Name", 32),
        ("Cuisine", 14),
        ("Region", 10),
        ("Mgmt", 12),
        ("Install", 11),
        ("Tenure (d)", 11),
        ("OSW", 7),
        ("GOV/wk", 9),
        ("Why", 22),
    ]
    header = " | ".join(name.ljust(w) for name, w in cols)
    print(header)
    print("-+-".join("-" * w for _, w in cols))
    for i, r in enumerate(picked, 1):
        tenure = (date.today() - date.fromisoformat(r["windows"]["post_start"])).days
        row = [
            str(i),
            str(r["STORE_ID"]),
            (r.get("STORE_NAME") or "")[:32],
            r["cuisine_bucket"],
            r["region_bucket"],
            r["mgmt_bucket"][:12],
            r["INSTALL_DATE"],
            str(tenure),
            f"{float(r['LIFETIME_OSW']):.0f}",
            f"${float(r['LIFETIME_GOV_STORE_WEEK']):.0f}",
            r["selection_reason"],
        ]
        line = " | ".join(str(v)[:w].ljust(w) for v, (_, w) in zip(row, cols))
        print(line)


def diversity_summary(picked: list[dict]) -> str:
    by_cuisine = defaultdict(int)
    by_region = defaultdict(int)
    by_mgmt = defaultdict(int)
    for r in picked:
        by_cuisine[r["cuisine_bucket"]] += 1
        by_region[r["region_bucket"]] += 1
        by_mgmt[r["mgmt_bucket"]] += 1

    def fmt(d):
        return ", ".join(f"{k}={v}" for k, v in sorted(d.items(), key=lambda x: -x[1]))

    return (
        f"Cuisines ({len(by_cuisine)}): {fmt(by_cuisine)}\n"
        f"Regions  ({len(by_region)}): {fmt(by_region)}\n"
        f"Mgmt     ({len(by_mgmt)}): {fmt(by_mgmt)}"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--exclude", nargs="*", default=[], help="Store IDs to exclude")
    parser.add_argument("--target", type=int, default=10, help="Cohort size (default 10)")
    parser.add_argument("--print-only", action="store_true", help="Print, don't write cohort.json")
    args = parser.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Running cohort SQL (>=180 active days, >=300 lifetime OSW, install_date <= today-6M)...", file=sys.stderr)
    rows = run_snowflake(COHORT_SQL)
    print(f"Got {len(rows)} eligible mx.", file=sys.stderr)

    if not rows:
        print("No eligible mx returned. Check filters.", file=sys.stderr)
        sys.exit(1)

    rows = add_diversity_buckets(rows)

    exclude = {str(s) for s in args.exclude}
    picked = pick_diversified(rows, args.target, exclude)

    for r in picked:
        r["windows"] = compute_windows(r["INSTALL_DATE"], r.get("LAST_CARD_ORDER_DATE"))

    print()
    print_table(picked)
    print()
    print(diversity_summary(picked))
    print()

    if args.print_only:
        return

    cohort_path = DATA_DIR / "cohort.json"
    payload = {
        "generated_at": date.today().isoformat(),
        "criteria": {
            "min_active_days": 180,
            "min_lifetime_osw": 300,
            "min_tenure_since_install_months": 6,
            "country": "US",
        },
        "selection_rule": "diversified-by-cuisine-region-mgmt; top-OSW within fresh-triple, then relax region, then mgmt, then fill",
        "eligible_pool_size": len(rows),
        "target_size": args.target,
        "mx": picked,
    }
    cohort_path.write_text(json.dumps(payload, indent=2, default=str))
    print(f"\nWrote {cohort_path}")


if __name__ == "__main__":
    main()
