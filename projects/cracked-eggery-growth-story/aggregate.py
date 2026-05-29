#!/usr/bin/env python3
"""
Cracked Eggery growth story — aggregate raw blocks into per-store + brand totals.

For each store, produces:
  - Matched-window deltas (pre 58/79d vs post 58/79d)
  - Full pre vs post-to-date (for context)
  - Weekly run-rates (orders/wk, GOV/wk) for executive framing
  - Pathfinder POS volume (cumulative + per-week)

Brand roll-up sums matched and weekly metrics across both stores.

Usage: python3 aggregate.py
"""

from __future__ import annotations

import json
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"


def to_float(v, default=0.0):
    if v is None:
        return default
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def to_int(v, default=0):
    if v is None:
        return default
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return default


def pct_change(pre, post):
    if pre is None or pre == 0:
        return None
    return (post - pre) / pre * 100.0


def per_week(value, days):
    if not days:
        return 0.0
    return value * 7.0 / days


def aggregate_channels(rows, period="matched"):
    """
    Returns dict {channel: {pre_orders, pre_subtotal, post_orders, post_subtotal}}.
    Skips null/empty channels.
    """
    out = {}
    for r in rows:
        ch = r.get("CHANNEL")
        if not ch:
            continue
        out[ch] = {
            "pre_orders": to_int(r.get("PRE_ORDERS")),
            "pre_subtotal": to_float(r.get("PRE_SUBTOTAL")),
            "post_orders": to_int(r.get("POST_ORDERS")),
            "post_subtotal": to_float(r.get("POST_SUBTOTAL")),
        }
    return out


def aggregate_mp_ops(rows):
    if not rows:
        return {}
    r = rows[0]
    pre_completed = to_int(r.get("PRE_COMPLETED_ORDERS"))
    post_completed = to_int(r.get("POST_COMPLETED_ORDERS"))
    pre_errors = to_int(r.get("PRE_ERRORS"))
    post_errors = to_int(r.get("POST_ERRORS"))
    return {
        "pre_completed_orders": pre_completed,
        "post_completed_orders": post_completed,
        "pre_errors": pre_errors,
        "post_errors": post_errors,
        "pre_error_rate_pct": (pre_errors / pre_completed * 100.0) if pre_completed else None,
        "post_error_rate_pct": (post_errors / post_completed * 100.0) if post_completed else None,
        "pre_avoidable_wait_seconds": to_float(r.get("PRE_AVOIDABLE_WAIT_SECONDS"), 0) or None,
        "post_avoidable_wait_seconds": to_float(r.get("POST_AVOIDABLE_WAIT_SECONDS"), 0) or None,
        "pre_avg_rating": to_float(r.get("PRE_AVG_RATING"), 0) or None,
        "post_avg_rating": to_float(r.get("POST_AVG_RATING"), 0) or None,
    }


def aggregate_mp_cancels(rows, ops_summary):
    if not rows:
        return {}
    r = rows[0]
    pre_cancelled = to_int(r.get("PRE_CANCELLED"))
    post_cancelled = to_int(r.get("POST_CANCELLED"))
    pre_completed = ops_summary.get("pre_completed_orders", 0)
    post_completed = ops_summary.get("post_completed_orders", 0)
    pre_attempts = pre_completed + pre_cancelled
    post_attempts = post_completed + post_cancelled
    return {
        "pre_cancelled": pre_cancelled,
        "post_cancelled": post_cancelled,
        "pre_cancel_rate_pct": (pre_cancelled / pre_attempts * 100.0) if pre_attempts else None,
        "post_cancel_rate_pct": (post_cancelled / post_attempts * 100.0) if post_attempts else None,
    }


def aggregate_cx_acq(rows):
    """Returns {channel: {new: {pre_orders,...}, repeat: {...}}}."""
    out = {}
    for r in rows:
        ch = r.get("CHANNEL")
        ctype = r.get("CX_TYPE_WITHIN_STORE")
        if not ch or not ctype:
            continue
        out.setdefault(ch, {})[ctype] = {
            "pre_orders": to_int(r.get("PRE_ORDERS")),
            "pre_subtotal": to_float(r.get("PRE_SUBTOTAL")),
            "post_orders": to_int(r.get("POST_ORDERS")),
            "post_subtotal": to_float(r.get("POST_SUBTOTAL")),
        }
    return out


def aggregate_sl(rows):
    if not rows:
        return {}
    r = rows[0]
    pre_sales = to_float(r.get("PRE_SALES"))
    pre_ad = to_float(r.get("PRE_AD_SPEND"))
    post_sales = to_float(r.get("POST_SALES"))
    post_ad = to_float(r.get("POST_AD_SPEND"))
    return {
        "pre_impressions": to_int(r.get("PRE_IMPRESSIONS")),
        "pre_clicks": to_int(r.get("PRE_CLICKS")),
        "pre_orders": to_int(r.get("PRE_ORDERS")),
        "pre_sales": pre_sales,
        "pre_ad_spend": pre_ad,
        "pre_new_cx": to_int(r.get("PRE_NEW_CX")),
        "pre_roas": (pre_sales / pre_ad) if pre_ad else None,
        "post_impressions": to_int(r.get("POST_IMPRESSIONS")),
        "post_clicks": to_int(r.get("POST_CLICKS")),
        "post_orders": to_int(r.get("POST_ORDERS")),
        "post_sales": post_sales,
        "post_ad_spend": post_ad,
        "post_new_cx": to_int(r.get("POST_NEW_CX")),
        "post_roas": (post_sales / post_ad) if post_ad else None,
    }


def aggregate_promos(rows):
    if not rows:
        return {}
    r = rows[0]
    return {
        "pre_orders": to_int(r.get("PRE_ORDERS")),
        "pre_sales": to_float(r.get("PRE_SALES")),
        "pre_dd_funded_discount": to_float(r.get("PRE_DD_FUNDED_DISCOUNT")),
        "pre_mx_funded_discount": to_float(r.get("PRE_MX_FUNDED_DISCOUNT")),
        "pre_new_cx": to_int(r.get("PRE_NEW_CX")),
        "post_orders": to_int(r.get("POST_ORDERS")),
        "post_sales": to_float(r.get("POST_SALES")),
        "post_dd_funded_discount": to_float(r.get("POST_DD_FUNDED_DISCOUNT")),
        "post_mx_funded_discount": to_float(r.get("POST_MX_FUNDED_DISCOUNT")),
        "post_new_cx": to_int(r.get("POST_NEW_CX")),
    }


def build_store_summary(raw):
    """Compute aggregates and rates for a single store."""
    w = raw["windows"]
    matched_pre_days = w["matched_pre_days"]
    post_days = w["post_days"]
    full_pre_days = w["full_pre_days"]

    channels_matched = aggregate_channels(raw["blocks"]["channel_matched"]["rows"])
    channels_full = aggregate_channels(raw["blocks"]["channel_full_pre_post"]["rows"])
    mp_ops = aggregate_mp_ops(raw["blocks"]["mp_ops"]["rows"])
    mp_cancels = aggregate_mp_cancels(raw["blocks"]["mp_cancellations"]["rows"], mp_ops)
    cx_acq = aggregate_cx_acq(raw["blocks"]["customer_acquisition"]["rows"])
    sl = aggregate_sl(raw["blocks"]["sponsored_listings"]["rows"])
    promos = aggregate_promos(raw["blocks"]["promos"]["rows"])

    # POS volume = In-store + Kiosk channels in the post window
    pos_orders = 0
    pos_gov = 0.0
    for ch in ("In-store", "Kiosk"):
        cell = channels_matched.get(ch)
        if cell:
            pos_orders += cell["post_orders"]
            pos_gov += cell["post_subtotal"]

    # Marketplace + Storefront totals (matched)
    mp_matched = channels_matched.get("Marketplace", {})
    sf_matched = channels_matched.get("Storefront", {})

    # Totals across non-POS channels (i.e., what DD-side business looked like)
    def sum_non_pos(channels):
        tot_pre_orders = tot_pre_gov = tot_post_orders = tot_post_gov = 0
        for ch, vals in channels.items():
            if ch in ("In-store", "Kiosk"):
                continue
            tot_pre_orders += vals["pre_orders"]
            tot_pre_gov += vals["pre_subtotal"]
            tot_post_orders += vals["post_orders"]
            tot_post_gov += vals["post_subtotal"]
        return tot_pre_orders, tot_pre_gov, tot_post_orders, tot_post_gov

    nonpos_pre_orders_m, nonpos_pre_gov_m, nonpos_post_orders_m, nonpos_post_gov_m = sum_non_pos(channels_matched)
    nonpos_pre_orders_f, nonpos_pre_gov_f, nonpos_post_orders_f, nonpos_post_gov_f = sum_non_pos(channels_full)

    # New cx counts (MP+Storefront)
    new_cx_pre = new_cx_post = 0
    repeat_cx_pre = repeat_cx_post = 0
    for ch, types in cx_acq.items():
        if "new" in types:
            new_cx_pre += types["new"]["pre_orders"]
            new_cx_post += types["new"]["post_orders"]
        if "repeat" in types:
            repeat_cx_pre += types["repeat"]["pre_orders"]
            repeat_cx_post += types["repeat"]["post_orders"]

    return {
        "store_id": raw["store_id"],
        "store_name": raw["store_name"],
        "install_date": raw["install_date"],
        "tenure_days": raw["tenure_days"],
        "windows": w,
        "metadata": raw["metadata"],
        "channels_matched": channels_matched,
        "channels_full": channels_full,
        "mp_ops": mp_ops,
        "mp_cancels": mp_cancels,
        "cx_acq": cx_acq,
        "sl": sl,
        "promos": promos,
        "totals": {
            "post_pos_orders": pos_orders,
            "post_pos_gov": pos_gov,
            "post_pos_orders_per_week": per_week(pos_orders, post_days),
            "post_pos_gov_per_week": per_week(pos_gov, post_days),
            "post_pos_gov_annualized": pos_gov * 365.0 / post_days if post_days else 0,
            # Matched marketplace+storefront (non-POS)
            "matched_nonpos_pre_orders": nonpos_pre_orders_m,
            "matched_nonpos_post_orders": nonpos_post_orders_m,
            "matched_nonpos_pre_gov": nonpos_pre_gov_m,
            "matched_nonpos_post_gov": nonpos_post_gov_m,
            "matched_nonpos_orders_delta_pct": pct_change(nonpos_pre_orders_m, nonpos_post_orders_m),
            "matched_nonpos_gov_delta_pct": pct_change(nonpos_pre_gov_m, nonpos_post_gov_m),
            # Same, normalized to per-week (lets us account for slightly different
            # window lengths if we ever need to)
            "matched_nonpos_pre_gov_per_week": per_week(nonpos_pre_gov_m, matched_pre_days),
            "matched_nonpos_post_gov_per_week": per_week(nonpos_post_gov_m, post_days),
            # Full pre / post-to-date (with weekly normalization since lengths differ)
            "full_pre_nonpos_orders_per_week": per_week(nonpos_pre_orders_f, full_pre_days),
            "full_pre_nonpos_gov_per_week": per_week(nonpos_pre_gov_f, full_pre_days),
            "post_nonpos_orders_per_week": per_week(nonpos_post_orders_f, post_days),
            "post_nonpos_gov_per_week": per_week(nonpos_post_gov_f, post_days),
            # New cx — matched
            "matched_new_cx_pre": new_cx_pre,
            "matched_new_cx_post": new_cx_post,
            "matched_new_cx_delta_pct": pct_change(new_cx_pre, new_cx_post),
            "matched_repeat_cx_pre": repeat_cx_pre,
            "matched_repeat_cx_post": repeat_cx_post,
            "matched_repeat_cx_delta_pct": pct_change(repeat_cx_pre, repeat_cx_post),
        },
    }


def sum_channels(channels_a, channels_b):
    """Sum two channel dicts (matched-window pre/post)."""
    keys = set(channels_a) | set(channels_b)
    out = {}
    for k in keys:
        a = channels_a.get(k, {})
        b = channels_b.get(k, {})
        out[k] = {
            "pre_orders": a.get("pre_orders", 0) + b.get("pre_orders", 0),
            "pre_subtotal": a.get("pre_subtotal", 0) + b.get("pre_subtotal", 0),
            "post_orders": a.get("post_orders", 0) + b.get("post_orders", 0),
            "post_subtotal": a.get("post_subtotal", 0) + b.get("post_subtotal", 0),
        }
    return out


def build_brand_summary(stores):
    """Sum totals across both stores. Channels summed at matched-window level."""
    channels_matched = {}
    channels_full = {}
    for s in stores:
        channels_matched = sum_channels(channels_matched, s["channels_matched"]) if channels_matched else dict(s["channels_matched"])
        channels_full = sum_channels(channels_full, s["channels_full"]) if channels_full else dict(s["channels_full"])

    # SL / promos summed
    def sum_dicts(key, numeric_keys):
        out = {k: 0 for k in numeric_keys}
        for s in stores:
            d = s.get(key, {}) or {}
            for k in numeric_keys:
                out[k] = (out[k] or 0) + (d.get(k) or 0)
        return out

    sl_keys = [
        "pre_impressions", "pre_clicks", "pre_orders", "pre_sales", "pre_ad_spend", "pre_new_cx",
        "post_impressions", "post_clicks", "post_orders", "post_sales", "post_ad_spend", "post_new_cx",
    ]
    sl = sum_dicts("sl", sl_keys)
    sl["pre_roas"] = (sl["pre_sales"] / sl["pre_ad_spend"]) if sl["pre_ad_spend"] else None
    sl["post_roas"] = (sl["post_sales"] / sl["post_ad_spend"]) if sl["post_ad_spend"] else None

    promo_keys = [
        "pre_orders", "pre_sales", "pre_dd_funded_discount", "pre_mx_funded_discount", "pre_new_cx",
        "post_orders", "post_sales", "post_dd_funded_discount", "post_mx_funded_discount", "post_new_cx",
    ]
    promos = sum_dicts("promos", promo_keys)

    # MP ops — combine errors and completed; recompute rates
    pre_completed = sum(s["mp_ops"].get("pre_completed_orders", 0) for s in stores)
    post_completed = sum(s["mp_ops"].get("post_completed_orders", 0) for s in stores)
    pre_errors = sum(s["mp_ops"].get("pre_errors", 0) for s in stores)
    post_errors = sum(s["mp_ops"].get("post_errors", 0) for s in stores)
    pre_cancelled = sum(s["mp_cancels"].get("pre_cancelled", 0) for s in stores)
    post_cancelled = sum(s["mp_cancels"].get("post_cancelled", 0) for s in stores)
    pre_attempts = pre_completed + pre_cancelled
    post_attempts = post_completed + post_cancelled

    # Wait/rating: weighted avg by completed orders
    def weighted_avg(values_weights):
        wsum = sum(w for _, w in values_weights if w)
        if not wsum:
            return None
        return sum((v or 0) * (w or 0) for v, w in values_weights) / wsum

    mp_ops_brand = {
        "pre_completed_orders": pre_completed,
        "post_completed_orders": post_completed,
        "pre_errors": pre_errors,
        "post_errors": post_errors,
        "pre_error_rate_pct": (pre_errors / pre_completed * 100.0) if pre_completed else None,
        "post_error_rate_pct": (post_errors / post_completed * 100.0) if post_completed else None,
        "pre_avoidable_wait_seconds": weighted_avg([
            (s["mp_ops"].get("pre_avoidable_wait_seconds"), s["mp_ops"].get("pre_completed_orders", 0))
            for s in stores
        ]),
        "post_avoidable_wait_seconds": weighted_avg([
            (s["mp_ops"].get("post_avoidable_wait_seconds"), s["mp_ops"].get("post_completed_orders", 0))
            for s in stores
        ]),
        "pre_avg_rating": weighted_avg([
            (s["mp_ops"].get("pre_avg_rating"), s["mp_ops"].get("pre_completed_orders", 0))
            for s in stores
        ]),
        "post_avg_rating": weighted_avg([
            (s["mp_ops"].get("post_avg_rating"), s["mp_ops"].get("post_completed_orders", 0))
            for s in stores
        ]),
    }

    mp_cancels_brand = {
        "pre_cancelled": pre_cancelled,
        "post_cancelled": post_cancelled,
        "pre_cancel_rate_pct": (pre_cancelled / pre_attempts * 100.0) if pre_attempts else None,
        "post_cancel_rate_pct": (post_cancelled / post_attempts * 100.0) if post_attempts else None,
    }

    # Totals
    pos_orders = sum(s["totals"]["post_pos_orders"] for s in stores)
    pos_gov = sum(s["totals"]["post_pos_gov"] for s in stores)
    matched_nonpos_pre_gov = sum(s["totals"]["matched_nonpos_pre_gov"] for s in stores)
    matched_nonpos_post_gov = sum(s["totals"]["matched_nonpos_post_gov"] for s in stores)
    matched_nonpos_pre_orders = sum(s["totals"]["matched_nonpos_pre_orders"] for s in stores)
    matched_nonpos_post_orders = sum(s["totals"]["matched_nonpos_post_orders"] for s in stores)
    matched_new_cx_pre = sum(s["totals"]["matched_new_cx_pre"] for s in stores)
    matched_new_cx_post = sum(s["totals"]["matched_new_cx_post"] for s in stores)
    matched_repeat_cx_pre = sum(s["totals"]["matched_repeat_cx_pre"] for s in stores)
    matched_repeat_cx_post = sum(s["totals"]["matched_repeat_cx_post"] for s in stores)

    # Weekly run-rate for full-pre and post
    full_pre_nonpos_gov_per_week = sum(s["totals"]["full_pre_nonpos_gov_per_week"] for s in stores)
    full_pre_nonpos_orders_per_week = sum(s["totals"]["full_pre_nonpos_orders_per_week"] for s in stores)
    post_nonpos_gov_per_week = sum(s["totals"]["post_nonpos_gov_per_week"] for s in stores)
    post_nonpos_orders_per_week = sum(s["totals"]["post_nonpos_orders_per_week"] for s in stores)

    # Annualized POS run rate
    post_pos_gov_per_week = sum(s["totals"]["post_pos_gov_per_week"] for s in stores)
    post_pos_gov_annualized = sum(s["totals"]["post_pos_gov_annualized"] for s in stores)

    return {
        "store_count": len(stores),
        "channels_matched": channels_matched,
        "channels_full": channels_full,
        "mp_ops": mp_ops_brand,
        "mp_cancels": mp_cancels_brand,
        "sl": sl,
        "promos": promos,
        "totals": {
            "post_pos_orders": pos_orders,
            "post_pos_gov": pos_gov,
            "post_pos_gov_per_week": post_pos_gov_per_week,
            "post_pos_gov_annualized": post_pos_gov_annualized,
            "matched_nonpos_pre_gov": matched_nonpos_pre_gov,
            "matched_nonpos_post_gov": matched_nonpos_post_gov,
            "matched_nonpos_pre_orders": matched_nonpos_pre_orders,
            "matched_nonpos_post_orders": matched_nonpos_post_orders,
            "matched_nonpos_gov_delta_pct": pct_change(matched_nonpos_pre_gov, matched_nonpos_post_gov),
            "matched_nonpos_orders_delta_pct": pct_change(matched_nonpos_pre_orders, matched_nonpos_post_orders),
            "matched_new_cx_pre": matched_new_cx_pre,
            "matched_new_cx_post": matched_new_cx_post,
            "matched_new_cx_delta_pct": pct_change(matched_new_cx_pre, matched_new_cx_post),
            "matched_repeat_cx_pre": matched_repeat_cx_pre,
            "matched_repeat_cx_post": matched_repeat_cx_post,
            "matched_repeat_cx_delta_pct": pct_change(matched_repeat_cx_pre, matched_repeat_cx_post),
            "full_pre_nonpos_gov_per_week": full_pre_nonpos_gov_per_week,
            "post_nonpos_gov_per_week": post_nonpos_gov_per_week,
            "full_pre_nonpos_orders_per_week": full_pre_nonpos_orders_per_week,
            "post_nonpos_orders_per_week": post_nonpos_orders_per_week,
            "nonpos_gov_weekly_delta_pct_vs_full_pre": pct_change(full_pre_nonpos_gov_per_week, post_nonpos_gov_per_week),
            "nonpos_orders_weekly_delta_pct_vs_full_pre": pct_change(full_pre_nonpos_orders_per_week, post_nonpos_orders_per_week),
        },
    }


def main():
    cohort = json.loads((DATA_DIR / "cohort.json").read_text())

    stores = []
    for mx in cohort["mx"]:
        raw_path = RAW_DIR / f"{mx['STORE_ID']}.json"
        if not raw_path.exists():
            print(f"Missing raw file: {raw_path}")
            continue
        raw = json.loads(raw_path.read_text())
        stores.append(build_store_summary(raw))

    brand = build_brand_summary(stores)

    out = {
        "generated_at": cohort["generated_at"],
        "today": cohort["today"],
        "post_end_anchor": cohort["post_end_anchor"],
        "stores": stores,
        "brand": brand,
    }

    (DATA_DIR / "aggregate.json").write_text(json.dumps(out, indent=2, default=str))
    print(f"Wrote {DATA_DIR / 'aggregate.json'}")

    # Stdout summary
    print(f"\n--- Brand totals (matched window) ---")
    t = brand["totals"]
    print(f"  POS (post-only): {t['post_pos_orders']:,} orders | ${t['post_pos_gov']:,.0f} GOV | ${t['post_pos_gov_per_week']:,.0f}/wk | ${t['post_pos_gov_annualized']:,.0f}/yr run-rate")
    print(f"  Non-POS GOV: ${t['matched_nonpos_pre_gov']:,.0f} -> ${t['matched_nonpos_post_gov']:,.0f} ({t['matched_nonpos_gov_delta_pct']:+.1f}%)")
    print(f"  Non-POS orders: {t['matched_nonpos_pre_orders']:,} -> {t['matched_nonpos_post_orders']:,} ({t['matched_nonpos_orders_delta_pct']:+.1f}%)")
    print(f"  New cx: {t['matched_new_cx_pre']:,} -> {t['matched_new_cx_post']:,} ({t['matched_new_cx_delta_pct']:+.1f}%)")
    print(f"  Repeat cx: {t['matched_repeat_cx_pre']:,} -> {t['matched_repeat_cx_post']:,} ({t['matched_repeat_cx_delta_pct']:+.1f}%)")
    print(f"  SL ROAS: {brand['sl']['pre_roas']} -> {brand['sl']['post_roas']}")


if __name__ == "__main__":
    main()
