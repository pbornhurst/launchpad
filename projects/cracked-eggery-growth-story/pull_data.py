#!/usr/bin/env python3
"""
Cracked Eggery growth story — per-store Snowflake pull.

Adapted from projects/pathfinder-lift-study/pull_lift_data.py for short
tenure (~2 months on Pathfinder). Adds a 'matched_pre' window (same length
as the post window) so we can do apples-to-apples deltas, and keeps the
full 6mo pre window for context / seasonality.

Blocks:
  1. channel_full_pre_post  — MP/1p/InStore/Kiosk orders + GOV, 6M pre vs post-to-date
  2. channel_matched        — same channels, matched-length pre vs post
  3. mp_ops                 — MP avoidable wait, errors, rating (matched window)
  4. mp_cancellations       — MP cancellations (matched window)
  5. customer_acquisition   — MP+Storefront new vs repeat (matched window)
  6. sponsored_listings     — impressions, clicks, orders, sales, ad fee (matched + full)
  7. promos                 — promos + funded discounts (matched + full)

Usage:
  python3 pull_data.py
  python3 pull_data.py --force 2290148
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"

sys.path.insert(0, str(REPO_ROOT / "scripts"))
import snowflake_query as snow  # noqa: E402


def serialize(v):
    if v is None:
        return None
    if isinstance(v, (int, float, str, bool)):
        return v
    return str(v)


def run(conn, sql):
    cur = conn.cursor()
    try:
        cur.execute(sql)
        cols = [d[0] for d in cur.description] if cur.description else []
        rows = cur.fetchall()
        return [dict(zip(cols, [serialize(v) for v in r])) for r in rows]
    finally:
        cur.close()


# ------------------------------------------------------------------ blocks


def sql_channel_full_pre_post(store_id, w):
    """6mo pre vs post-to-date by channel. is_filtered=TRUE = completed orders only."""
    return f"""
    SELECT
      channel,
      SUM(CASE WHEN active_date BETWEEN '{w['pre_start']}' AND '{w['pre_end']}' THEN 1 ELSE 0 END) AS pre_orders,
      SUM(CASE WHEN active_date BETWEEN '{w['pre_start']}' AND '{w['pre_end']}' THEN subtotal ELSE 0 END) AS pre_subtotal,
      SUM(CASE WHEN active_date BETWEEN '{w['post_start']}' AND '{w['post_end']}' THEN 1 ELSE 0 END) AS post_orders,
      SUM(CASE WHEN active_date BETWEEN '{w['post_start']}' AND '{w['post_end']}' THEN subtotal ELSE 0 END) AS post_subtotal
    FROM edw.merchant.fact_merchant_orders_portal
    WHERE store_id = {store_id}
      AND active_date BETWEEN '{w['pre_start']}' AND '{w['post_end']}'
      AND is_filtered = TRUE
    GROUP BY channel
    ORDER BY channel
    LIMIT 50
    """


def sql_channel_matched(store_id, w):
    """Matched-length pre vs post by channel."""
    return f"""
    SELECT
      channel,
      SUM(CASE WHEN active_date BETWEEN '{w['matched_pre_start']}' AND '{w['matched_pre_end']}' THEN 1 ELSE 0 END) AS pre_orders,
      SUM(CASE WHEN active_date BETWEEN '{w['matched_pre_start']}' AND '{w['matched_pre_end']}' THEN subtotal ELSE 0 END) AS pre_subtotal,
      SUM(CASE WHEN active_date BETWEEN '{w['post_start']}' AND '{w['post_end']}' THEN 1 ELSE 0 END) AS post_orders,
      SUM(CASE WHEN active_date BETWEEN '{w['post_start']}' AND '{w['post_end']}' THEN subtotal ELSE 0 END) AS post_subtotal
    FROM edw.merchant.fact_merchant_orders_portal
    WHERE store_id = {store_id}
      AND active_date BETWEEN '{w['matched_pre_start']}' AND '{w['post_end']}'
      AND is_filtered = TRUE
    GROUP BY channel
    ORDER BY channel
    LIMIT 50
    """


def sql_mp_ops(store_id, w):
    """Marketplace ops — matched pre vs post. Errors/rating/wait only defined on completed orders."""
    return f"""
    SELECT
      SUM(CASE WHEN active_date BETWEEN '{w['matched_pre_start']}' AND '{w['matched_pre_end']}' THEN 1 ELSE 0 END) AS pre_completed_orders,
      SUM(CASE WHEN active_date BETWEEN '{w['matched_pre_start']}' AND '{w['matched_pre_end']}' THEN is_missing_incorrect_int ELSE 0 END) AS pre_errors,
      AVG(CASE WHEN active_date BETWEEN '{w['matched_pre_start']}' AND '{w['matched_pre_end']}' AND dasher_avoidable_wait_duration > 0 THEN dasher_avoidable_wait_duration END) AS pre_avoidable_wait_seconds,
      AVG(CASE WHEN active_date BETWEEN '{w['matched_pre_start']}' AND '{w['matched_pre_end']}' AND merchant_rating IS NOT NULL THEN merchant_rating END) AS pre_avg_rating,
      SUM(CASE WHEN active_date BETWEEN '{w['post_start']}' AND '{w['post_end']}' THEN 1 ELSE 0 END) AS post_completed_orders,
      SUM(CASE WHEN active_date BETWEEN '{w['post_start']}' AND '{w['post_end']}' THEN is_missing_incorrect_int ELSE 0 END) AS post_errors,
      AVG(CASE WHEN active_date BETWEEN '{w['post_start']}' AND '{w['post_end']}' AND dasher_avoidable_wait_duration > 0 THEN dasher_avoidable_wait_duration END) AS post_avoidable_wait_seconds,
      AVG(CASE WHEN active_date BETWEEN '{w['post_start']}' AND '{w['post_end']}' AND merchant_rating IS NOT NULL THEN merchant_rating END) AS post_avg_rating
    FROM edw.merchant.fact_merchant_orders_portal
    WHERE store_id = {store_id}
      AND active_date BETWEEN '{w['matched_pre_start']}' AND '{w['post_end']}'
      AND channel = 'Marketplace'
      AND is_filtered = TRUE
    LIMIT 5
    """


def sql_mp_cancellations(store_id, w):
    """Marketplace cancellations — matched pre vs post."""
    return f"""
    SELECT
      SUM(CASE WHEN active_date BETWEEN '{w['matched_pre_start']}' AND '{w['matched_pre_end']}' THEN 1 ELSE 0 END) AS pre_cancelled,
      SUM(CASE WHEN active_date BETWEEN '{w['post_start']}' AND '{w['post_end']}' THEN 1 ELSE 0 END) AS post_cancelled
    FROM edw.merchant.fact_merchant_orders_portal
    WHERE store_id = {store_id}
      AND active_date BETWEEN '{w['matched_pre_start']}' AND '{w['post_end']}'
      AND channel = 'Marketplace'
      AND is_filtered = FALSE
      AND is_cancelled_int = 1
    LIMIT 5
    """


def sql_customer_acquisition(store_id, w):
    """New vs repeat customers across MP+Storefront — matched pre vs post."""
    return f"""
    SELECT
      channel,
      cx_type_within_store,
      SUM(CASE WHEN active_date BETWEEN '{w['matched_pre_start']}' AND '{w['matched_pre_end']}' THEN 1 ELSE 0 END) AS pre_orders,
      SUM(CASE WHEN active_date BETWEEN '{w['matched_pre_start']}' AND '{w['matched_pre_end']}' THEN subtotal ELSE 0 END) AS pre_subtotal,
      SUM(CASE WHEN active_date BETWEEN '{w['post_start']}' AND '{w['post_end']}' THEN 1 ELSE 0 END) AS post_orders,
      SUM(CASE WHEN active_date BETWEEN '{w['post_start']}' AND '{w['post_end']}' THEN subtotal ELSE 0 END) AS post_subtotal
    FROM edw.merchant.fact_merchant_orders_portal
    WHERE store_id = {store_id}
      AND active_date BETWEEN '{w['matched_pre_start']}' AND '{w['post_end']}'
      AND channel IN ('Marketplace', 'Storefront')
      AND is_filtered = TRUE
      AND cx_type_within_store IN ('new', 'repeat')
    GROUP BY channel, cx_type_within_store
    ORDER BY channel, cx_type_within_store
    LIMIT 20
    """


def sql_sponsored_listings(store_id, w):
    """SL matched pre vs post. Amounts in cents."""
    return f"""
    SELECT
      SUM(CASE WHEN snapshot_date BETWEEN '{w['matched_pre_start']}' AND '{w['matched_pre_end']}' THEN impression_count ELSE 0 END) AS pre_impressions,
      SUM(CASE WHEN snapshot_date BETWEEN '{w['matched_pre_start']}' AND '{w['matched_pre_end']}' THEN click_count ELSE 0 END) AS pre_clicks,
      SUM(CASE WHEN snapshot_date BETWEEN '{w['matched_pre_start']}' AND '{w['matched_pre_end']}' THEN total_cx_count ELSE 0 END) AS pre_orders,
      SUM(CASE WHEN snapshot_date BETWEEN '{w['matched_pre_start']}' AND '{w['matched_pre_end']}' THEN total_cx_sales_amount_local ELSE 0 END) / 100.0 AS pre_sales,
      SUM(CASE WHEN snapshot_date BETWEEN '{w['matched_pre_start']}' AND '{w['matched_pre_end']}' THEN total_cx_ad_fee_local ELSE 0 END) / 100.0 AS pre_ad_spend,
      SUM(CASE WHEN snapshot_date BETWEEN '{w['matched_pre_start']}' AND '{w['matched_pre_end']}' THEN new_cx_count ELSE 0 END) AS pre_new_cx,
      SUM(CASE WHEN snapshot_date BETWEEN '{w['post_start']}' AND '{w['post_end']}' THEN impression_count ELSE 0 END) AS post_impressions,
      SUM(CASE WHEN snapshot_date BETWEEN '{w['post_start']}' AND '{w['post_end']}' THEN click_count ELSE 0 END) AS post_clicks,
      SUM(CASE WHEN snapshot_date BETWEEN '{w['post_start']}' AND '{w['post_end']}' THEN total_cx_count ELSE 0 END) AS post_orders,
      SUM(CASE WHEN snapshot_date BETWEEN '{w['post_start']}' AND '{w['post_end']}' THEN total_cx_sales_amount_local ELSE 0 END) / 100.0 AS post_sales,
      SUM(CASE WHEN snapshot_date BETWEEN '{w['post_start']}' AND '{w['post_end']}' THEN total_cx_ad_fee_local ELSE 0 END) / 100.0 AS post_ad_spend,
      SUM(CASE WHEN snapshot_date BETWEEN '{w['post_start']}' AND '{w['post_end']}' THEN new_cx_count ELSE 0 END) AS post_new_cx
    FROM edw.ads.fact_sl_campaign_performance
    WHERE store_id = {store_id}
      AND snapshot_date BETWEEN '{w['matched_pre_start']}' AND '{w['post_end']}'
      AND report_type = 'campaign_store'
      AND timezone_type = 'utc'
      AND daypart_name = 'day'
    LIMIT 5
    """


def sql_promos(store_id, w):
    """Promos matched pre vs post. Amounts in cents."""
    return f"""
    SELECT
      SUM(CASE WHEN snapshot_date BETWEEN '{w['matched_pre_start']}' AND '{w['matched_pre_end']}' THEN total_cx_count ELSE 0 END) AS pre_orders,
      SUM(CASE WHEN snapshot_date BETWEEN '{w['matched_pre_start']}' AND '{w['matched_pre_end']}' THEN total_cx_sales_amount_local ELSE 0 END) / 100.0 AS pre_sales,
      SUM(CASE WHEN snapshot_date BETWEEN '{w['matched_pre_start']}' AND '{w['matched_pre_end']}' THEN total_cx_dd_funded_discount_local ELSE 0 END) / 100.0 AS pre_dd_funded_discount,
      SUM(CASE WHEN snapshot_date BETWEEN '{w['matched_pre_start']}' AND '{w['matched_pre_end']}' THEN total_cx_mx_funded_discount_local ELSE 0 END) / 100.0 AS pre_mx_funded_discount,
      SUM(CASE WHEN snapshot_date BETWEEN '{w['matched_pre_start']}' AND '{w['matched_pre_end']}' THEN new_cx_count ELSE 0 END) AS pre_new_cx,
      SUM(CASE WHEN snapshot_date BETWEEN '{w['post_start']}' AND '{w['post_end']}' THEN total_cx_count ELSE 0 END) AS post_orders,
      SUM(CASE WHEN snapshot_date BETWEEN '{w['post_start']}' AND '{w['post_end']}' THEN total_cx_sales_amount_local ELSE 0 END) / 100.0 AS post_sales,
      SUM(CASE WHEN snapshot_date BETWEEN '{w['post_start']}' AND '{w['post_end']}' THEN total_cx_dd_funded_discount_local ELSE 0 END) / 100.0 AS post_dd_funded_discount,
      SUM(CASE WHEN snapshot_date BETWEEN '{w['post_start']}' AND '{w['post_end']}' THEN total_cx_mx_funded_discount_local ELSE 0 END) / 100.0 AS post_mx_funded_discount,
      SUM(CASE WHEN snapshot_date BETWEEN '{w['post_start']}' AND '{w['post_end']}' THEN new_cx_count ELSE 0 END) AS post_new_cx
    FROM edw.ads.fact_promo_campaign_performance
    WHERE store_id = {store_id}
      AND snapshot_date BETWEEN '{w['matched_pre_start']}' AND '{w['post_end']}'
      AND report_type = 'campaign_store'
      AND timezone_type = 'utc'
      AND daypart_name = 'day'
    LIMIT 5
    """


BLOCKS = [
    ("channel_full_pre_post", sql_channel_full_pre_post),
    ("channel_matched", sql_channel_matched),
    ("mp_ops", sql_mp_ops),
    ("mp_cancellations", sql_mp_cancellations),
    ("customer_acquisition", sql_customer_acquisition),
    ("sponsored_listings", sql_sponsored_listings),
    ("promos", sql_promos),
]


def pull_one(mx, raw_path):
    store_id = mx["STORE_ID"]
    w = mx["windows"]
    started = time.time()

    conn = snow.get_connection()
    out = {
        "store_id": store_id,
        "store_name": mx.get("STORE_NAME"),
        "business_id": mx.get("BUSINESS_ID"),
        "install_date": mx.get("INSTALL_DATE"),
        "tenure_days": mx.get("TENURE_DAYS"),
        "windows": w,
        "metadata": {
            "cuisine_type": mx.get("CUISINE_TYPE"),
            "region_name": mx.get("REGION_NAME"),
            "submarket_name": mx.get("SUBMARKET_NAME"),
            "management_type_grouped": mx.get("MANAGEMENT_TYPE_GROUPED"),
            "lifetime_card_orders": mx.get("LIFETIME_CARD_ORDERS"),
            "lifetime_card_gov": mx.get("LIFETIME_CARD_GOV"),
        },
        "blocks": {},
        "pulled_at": date.today().isoformat(),
    }
    try:
        for name, fn in BLOCKS:
            t0 = time.time()
            sql = fn(store_id, w)
            try:
                rows = run(conn, sql)
                out["blocks"][name] = {
                    "rows": rows,
                    "elapsed_s": round(time.time() - t0, 2),
                }
                print(f"  [{store_id}] {name}: {len(rows)} rows ({time.time()-t0:.1f}s)", file=sys.stderr)
            except Exception as e:
                out["blocks"][name] = {
                    "rows": [],
                    "error": str(e),
                    "elapsed_s": round(time.time() - t0, 2),
                }
                print(f"  [{store_id}] {name}: ERROR {e}", file=sys.stderr)
    finally:
        conn.close()

    raw_path.write_text(json.dumps(out, indent=2, default=str))
    elapsed = time.time() - started
    print(f"[{store_id}] DONE in {elapsed:.1f}s -> {raw_path.name}", file=sys.stderr)
    return store_id, elapsed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", nargs="*", default=[])
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--only", nargs="*", default=[])
    args = parser.parse_args()

    cohort = json.loads((DATA_DIR / "cohort.json").read_text())
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    force = {str(s) for s in args.force}
    only = {str(s) for s in args.only}

    pending = []
    for mx in cohort["mx"]:
        sid = str(mx["STORE_ID"])
        if only and sid not in only:
            continue
        raw_path = RAW_DIR / f"{sid}.json"
        if raw_path.exists() and sid not in force:
            print(f"[{sid}] skip (exists)", file=sys.stderr)
            continue
        pending.append((mx, raw_path))

    if not pending:
        print("Nothing to pull.", file=sys.stderr)
        return

    print(f"Pulling {len(pending)} stores with {args.workers} workers...", file=sys.stderr)
    started = time.time()
    errors = []

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(pull_one, mx, p): mx["STORE_ID"] for mx, p in pending}
        for fut in as_completed(futures):
            sid = futures[fut]
            try:
                fut.result()
            except Exception as e:
                errors.append((sid, str(e)))
                traceback.print_exc(file=sys.stderr)

    elapsed = time.time() - started
    print(f"\nDone in {elapsed:.1f}s. Pulled {len(pending) - len(errors)} / {len(pending)}.", file=sys.stderr)
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
