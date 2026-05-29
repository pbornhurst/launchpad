#!/usr/bin/env python3
"""
Pathfinder Lift Study — Phase 3: aggregation.

Reads data/raw/*.json (one per mx) and produces data/cohort_aggregate.json
with:
  - per_mx[]: per-mx structured lifts (channels, ops, customers, marketing, maturation)
  - cohort: cohort-wide rollups (sum-based + GOV-weighted lift %)
  - coverage_flags: per-mx data quality flags (thin pre period, $0 pre 1p, etc.)

Usage:
  python3 aggregate.py
"""

from __future__ import annotations

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
RAW_DIR = DATA_DIR / "raw"


def fnum(v):
    """Coerce a Snowflake-string-serialized number to float (None-safe)."""
    if v is None or v == "" or v == "None":
        return 0.0
    try:
        return float(v)
    except (ValueError, TypeError):
        return 0.0


def pct_change(post, pre):
    """Return (post-pre)/pre as a fraction. None if pre is 0 (division undefined)."""
    pre = fnum(pre)
    post = fnum(post)
    if pre <= 0:
        return None  # caller decides 'newly enabled' vs 'undefined'
    return (post - pre) / pre


def parse_per_mx(raw):
    """Pull a structured per-mx record out of a raw blob."""
    store_id = raw["store_id"]
    name = raw.get("store_name")
    meta = raw.get("metadata", {})
    blocks = raw.get("blocks", {})

    # ---- Block 1: channel pre/post (6M pre vs 6M post) ----
    channel_pp = {}
    for row in blocks.get("channel_pre_post", {}).get("rows", []):
        ch = row.get("CHANNEL")
        if not ch:
            continue
        channel_pp[ch] = {
            "pre_orders": int(fnum(row.get("PRE_ORDERS"))),
            "pre_subtotal": fnum(row.get("PRE_SUBTOTAL")),
            "post_orders": int(fnum(row.get("POST_ORDERS"))),
            "post_subtotal": fnum(row.get("POST_SUBTOTAL")),
        }
        e = channel_pp[ch]
        e["orders_lift_pct"] = pct_change(e["post_orders"], e["pre_orders"])
        e["gov_lift_pct"] = pct_change(e["post_subtotal"], e["pre_subtotal"])
        # AOVs
        e["pre_aov"] = (e["pre_subtotal"] / e["pre_orders"]) if e["pre_orders"] else 0
        e["post_aov"] = (e["post_subtotal"] / e["post_orders"]) if e["post_orders"] else 0

    # ---- Block 2: channel maturation (M1-3 vs M4-6 vs Latest 3M) ----
    channel_mat = {}
    for row in blocks.get("channel_maturation", {}).get("rows", []):
        ch = row.get("CHANNEL")
        if not ch:
            continue
        e = {
            "m1_3_orders": int(fnum(row.get("M1_3_ORDERS"))),
            "m1_3_subtotal": fnum(row.get("M1_3_SUBTOTAL")),
            "m4_6_orders": int(fnum(row.get("M4_6_ORDERS"))),
            "m4_6_subtotal": fnum(row.get("M4_6_SUBTOTAL")),
            "latest_3m_orders": int(fnum(row.get("LATEST_3M_ORDERS"))),
            "latest_3m_subtotal": fnum(row.get("LATEST_3M_SUBTOTAL")),
        }
        e["m4_6_vs_m1_3_orders_pct"] = pct_change(e["m4_6_orders"], e["m1_3_orders"])
        e["m4_6_vs_m1_3_gov_pct"] = pct_change(e["m4_6_subtotal"], e["m1_3_subtotal"])
        if e["latest_3m_orders"] > 0:
            e["latest_vs_m1_3_orders_pct"] = pct_change(e["latest_3m_orders"], e["m1_3_orders"])
            e["latest_vs_m1_3_gov_pct"] = pct_change(e["latest_3m_subtotal"], e["m1_3_subtotal"])
        channel_mat[ch] = e

    # ---- Block 3: marketplace ops (completed orders only) ----
    ops_row = next(iter(blocks.get("mp_ops", {}).get("rows", [])), {})
    # ---- Block 3b: marketplace cancellations (separate query) ----
    cancel_row = next(iter(blocks.get("mp_cancellations", {}).get("rows", [])), {})

    pre_completed = int(fnum(ops_row.get("PRE_COMPLETED_ORDERS")))
    post_completed = int(fnum(ops_row.get("POST_COMPLETED_ORDERS")))
    pre_cancelled = int(fnum(cancel_row.get("PRE_CANCELLED")))
    post_cancelled = int(fnum(cancel_row.get("POST_CANCELLED")))

    # dasher_avoidable_wait_duration is already in MINUTES (verified against actual data,
    # range ~0-17 minutes, mean ~2.6 minutes). Do not divide by 60.
    mp_ops = {
        "pre_completed_orders": pre_completed,
        "pre_cancelled": pre_cancelled,
        "pre_attempted": pre_completed + pre_cancelled,
        "pre_errors": int(fnum(ops_row.get("PRE_ERRORS"))),
        "pre_avoidable_wait_minutes": fnum(ops_row.get("PRE_AVOIDABLE_WAIT_SECONDS")),
        "pre_avg_rating": fnum(ops_row.get("PRE_AVG_RATING")),
        "post_completed_orders": post_completed,
        "post_cancelled": post_cancelled,
        "post_attempted": post_completed + post_cancelled,
        "post_errors": int(fnum(ops_row.get("POST_ERRORS"))),
        "post_avoidable_wait_minutes": fnum(ops_row.get("POST_AVOIDABLE_WAIT_SECONDS")),
        "post_avg_rating": fnum(ops_row.get("POST_AVG_RATING")),
    }
    # Cancel rate: cancelled / total attempted (completed + cancelled)
    mp_ops["pre_cancel_rate"] = (pre_cancelled / mp_ops["pre_attempted"]) if mp_ops["pre_attempted"] else 0
    mp_ops["post_cancel_rate"] = (post_cancelled / mp_ops["post_attempted"]) if mp_ops["post_attempted"] else 0
    # Error rate: errors / completed orders (the standard QBR definition)
    mp_ops["pre_error_rate"] = (mp_ops["pre_errors"] / pre_completed) if pre_completed else 0
    mp_ops["post_error_rate"] = (mp_ops["post_errors"] / post_completed) if post_completed else 0
    # Back-compat aliases (legacy code path expects pre_wait_minutes naming)
    mp_ops["pre_wait_minutes"] = mp_ops["pre_avoidable_wait_minutes"]
    mp_ops["post_wait_minutes"] = mp_ops["post_avoidable_wait_minutes"]
    # Aliases for backward compat with consumers expecting pre_orders/post_orders
    mp_ops["pre_orders"] = pre_completed
    mp_ops["post_orders"] = post_completed

    # ---- Block 4: customer acquisition (new vs repeat by channel) ----
    cust = {"new": {"pre_orders": 0, "pre_subtotal": 0, "post_orders": 0, "post_subtotal": 0},
            "repeat": {"pre_orders": 0, "pre_subtotal": 0, "post_orders": 0, "post_subtotal": 0}}
    cust_by_channel = {}
    for row in blocks.get("customer_acquisition", {}).get("rows", []):
        ch = row.get("CHANNEL")
        cxt = (row.get("CX_TYPE_WITHIN_STORE") or "").lower()
        if cxt not in ("new", "repeat"):
            continue
        cust[cxt]["pre_orders"] += int(fnum(row.get("PRE_ORDERS")))
        cust[cxt]["pre_subtotal"] += fnum(row.get("PRE_SUBTOTAL"))
        cust[cxt]["post_orders"] += int(fnum(row.get("POST_ORDERS")))
        cust[cxt]["post_subtotal"] += fnum(row.get("POST_SUBTOTAL"))
        cust_by_channel.setdefault(ch, {"new": {}, "repeat": {}})[cxt] = {
            "pre_orders": int(fnum(row.get("PRE_ORDERS"))),
            "pre_subtotal": fnum(row.get("PRE_SUBTOTAL")),
            "post_orders": int(fnum(row.get("POST_ORDERS"))),
            "post_subtotal": fnum(row.get("POST_SUBTOTAL")),
        }
    for cxt in ("new", "repeat"):
        cust[cxt]["orders_lift_pct"] = pct_change(cust[cxt]["post_orders"], cust[cxt]["pre_orders"])
        cust[cxt]["gov_lift_pct"] = pct_change(cust[cxt]["post_subtotal"], cust[cxt]["pre_subtotal"])

    # ---- Block 5: sponsored listings ----
    sl_row = next(iter(blocks.get("sponsored_listings", {}).get("rows", [])), {})
    sl = {
        "pre_impressions": int(fnum(sl_row.get("PRE_IMPRESSIONS"))),
        "pre_clicks": int(fnum(sl_row.get("PRE_CLICKS"))),
        "pre_orders": int(fnum(sl_row.get("PRE_ORDERS"))),
        "pre_sales": fnum(sl_row.get("PRE_SALES")),
        "pre_ad_spend": fnum(sl_row.get("PRE_AD_SPEND")),
        "pre_new_cx": int(fnum(sl_row.get("PRE_NEW_CX"))),
        "post_impressions": int(fnum(sl_row.get("POST_IMPRESSIONS"))),
        "post_clicks": int(fnum(sl_row.get("POST_CLICKS"))),
        "post_orders": int(fnum(sl_row.get("POST_ORDERS"))),
        "post_sales": fnum(sl_row.get("POST_SALES")),
        "post_ad_spend": fnum(sl_row.get("POST_AD_SPEND")),
        "post_new_cx": int(fnum(sl_row.get("POST_NEW_CX"))),
    }
    sl["pre_roas"] = (sl["pre_sales"] / sl["pre_ad_spend"]) if sl["pre_ad_spend"] else 0
    sl["post_roas"] = (sl["post_sales"] / sl["post_ad_spend"]) if sl["post_ad_spend"] else 0
    sl["pre_ctr"] = (sl["pre_clicks"] / sl["pre_impressions"]) if sl["pre_impressions"] else 0
    sl["post_ctr"] = (sl["post_clicks"] / sl["post_impressions"]) if sl["post_impressions"] else 0
    sl["new_cx_lift_pct"] = pct_change(sl["post_new_cx"], sl["pre_new_cx"])

    # ---- Block 6: promos ----
    promo_row = next(iter(blocks.get("promos", {}).get("rows", [])), {})
    promo = {
        "pre_orders": int(fnum(promo_row.get("PRE_ORDERS"))),
        "pre_sales": fnum(promo_row.get("PRE_SALES")),
        "pre_dd_funded_discount": fnum(promo_row.get("PRE_DD_FUNDED_DISCOUNT")),
        "pre_mx_funded_discount": fnum(promo_row.get("PRE_MX_FUNDED_DISCOUNT")),
        "pre_new_cx": int(fnum(promo_row.get("PRE_NEW_CX"))),
        "post_orders": int(fnum(promo_row.get("POST_ORDERS"))),
        "post_sales": fnum(promo_row.get("POST_SALES")),
        "post_dd_funded_discount": fnum(promo_row.get("POST_DD_FUNDED_DISCOUNT")),
        "post_mx_funded_discount": fnum(promo_row.get("POST_MX_FUNDED_DISCOUNT")),
        "post_new_cx": int(fnum(promo_row.get("POST_NEW_CX"))),
    }

    # ---- Coverage flags ----
    flags = []
    mp_pre = channel_pp.get("Marketplace", {}).get("pre_orders", 0)
    if mp_pre < 30:
        flags.append(f"thin_pre_mp_orders={mp_pre}")
    sf_pre = channel_pp.get("Storefront", {}).get("pre_subtotal", 0)
    if sf_pre == 0 and channel_pp.get("Storefront", {}).get("post_subtotal", 0) > 0:
        flags.append("storefront_newly_enabled_post_install")
    instore_pre = channel_pp.get("In-store", {}).get("pre_subtotal", 0)
    if instore_pre > 0:
        flags.append(f"unexpected_pre_instore_subtotal={instore_pre:.0f}")  # shouldn't happen

    # Roll up totals (all channels combined)
    pre_total_orders = sum(c["pre_orders"] for c in channel_pp.values())
    pre_total_gov = sum(c["pre_subtotal"] for c in channel_pp.values())
    post_total_orders = sum(c["post_orders"] for c in channel_pp.values())
    post_total_gov = sum(c["post_subtotal"] for c in channel_pp.values())

    # Pathfinder POS rollup = In-store + Kiosk (the channels Pathfinder enables).
    # Compute for both pre/post (where pre = 0 by definition) and maturation windows.
    pos_post_orders = (channel_pp.get("In-store", {}).get("post_orders", 0)
                       + channel_pp.get("Kiosk", {}).get("post_orders", 0))
    pos_post_gov = (channel_pp.get("In-store", {}).get("post_subtotal", 0)
                    + channel_pp.get("Kiosk", {}).get("post_subtotal", 0))
    pos_pre_orders = (channel_pp.get("In-store", {}).get("pre_orders", 0)
                      + channel_pp.get("Kiosk", {}).get("pre_orders", 0))
    pos_pre_gov = (channel_pp.get("In-store", {}).get("pre_subtotal", 0)
                   + channel_pp.get("Kiosk", {}).get("pre_subtotal", 0))

    mat_pos = {
        "m1_3_orders": (channel_mat.get("In-store", {}).get("m1_3_orders", 0)
                        + channel_mat.get("Kiosk", {}).get("m1_3_orders", 0)),
        "m1_3_subtotal": (channel_mat.get("In-store", {}).get("m1_3_subtotal", 0)
                          + channel_mat.get("Kiosk", {}).get("m1_3_subtotal", 0)),
        "m4_6_orders": (channel_mat.get("In-store", {}).get("m4_6_orders", 0)
                        + channel_mat.get("Kiosk", {}).get("m4_6_orders", 0)),
        "m4_6_subtotal": (channel_mat.get("In-store", {}).get("m4_6_subtotal", 0)
                          + channel_mat.get("Kiosk", {}).get("m4_6_subtotal", 0)),
        "latest_3m_orders": (channel_mat.get("In-store", {}).get("latest_3m_orders", 0)
                             + channel_mat.get("Kiosk", {}).get("latest_3m_orders", 0)),
        "latest_3m_subtotal": (channel_mat.get("In-store", {}).get("latest_3m_subtotal", 0)
                               + channel_mat.get("Kiosk", {}).get("latest_3m_subtotal", 0)),
    }
    mat_pos["m4_6_vs_m1_3_orders_pct"] = pct_change(mat_pos["m4_6_orders"], mat_pos["m1_3_orders"])
    mat_pos["m4_6_vs_m1_3_gov_pct"] = pct_change(mat_pos["m4_6_subtotal"], mat_pos["m1_3_subtotal"])
    if mat_pos["latest_3m_orders"] > 0:
        mat_pos["latest_vs_m1_3_orders_pct"] = pct_change(mat_pos["latest_3m_orders"], mat_pos["m1_3_orders"])
        mat_pos["latest_vs_m1_3_gov_pct"] = pct_change(mat_pos["latest_3m_subtotal"], mat_pos["m1_3_subtotal"])

    pathfinder_pos = {
        "pre_orders": pos_pre_orders,
        "pre_gov": pos_pre_gov,
        "post_orders": pos_post_orders,
        "post_gov": pos_post_gov,
        "orders_lift_pct": pct_change(pos_post_orders, pos_pre_orders),
        "gov_lift_pct": pct_change(pos_post_gov, pos_pre_gov),
        "maturation": mat_pos,
    }

    return {
        "store_id": store_id,
        "store_name": name,
        "install_date": raw.get("install_date"),
        "metadata": meta,
        "windows": raw.get("windows"),
        "channels_pre_post": channel_pp,
        "channels_maturation": channel_mat,
        "mp_ops": mp_ops,
        "customers": {
            "total": cust,
            "by_channel": cust_by_channel,
        },
        "sponsored_listings": sl,
        "promos": promo,
        "totals_pre_post": {
            "pre_orders": pre_total_orders,
            "pre_gov": pre_total_gov,
            "post_orders": post_total_orders,
            "post_gov": post_total_gov,
            "orders_lift_pct": pct_change(post_total_orders, pre_total_orders),
            "gov_lift_pct": pct_change(post_total_gov, pre_total_gov),
        },
        "pathfinder_pos": pathfinder_pos,
        "coverage_flags": flags,
    }


def cohort_aggregate(per_mx_records):
    """
    Build cohort-wide rollups from a list of per-mx records.

    For most metrics we sum-then-compare rather than average-of-percents
    so the rollup reflects business-weighted reality (one big mx + nine
    small ones still gives a $-weighted view).
    """
    sums = {
        "channels": {},  # channel -> {pre_orders, pre_gov, post_orders, post_gov, count_present}
        "channels_maturation": {},  # channel -> {m1_3_orders, m4_6_orders, ...}
        "mp_ops": {
            "pre_completed_orders": 0, "pre_cancelled": 0, "pre_errors": 0,
            "post_completed_orders": 0, "post_cancelled": 0, "post_errors": 0,
            "pre_wait_total": 0, "pre_wait_n": 0,
            "post_wait_total": 0, "post_wait_n": 0,
            "pre_rating_total": 0, "pre_rating_n": 0,
            "post_rating_total": 0, "post_rating_n": 0,
        },
        "customers": {
            "new": {"pre_orders": 0, "pre_subtotal": 0, "post_orders": 0, "post_subtotal": 0},
            "repeat": {"pre_orders": 0, "pre_subtotal": 0, "post_orders": 0, "post_subtotal": 0},
        },
        "sl": {
            "pre_impressions": 0, "pre_clicks": 0, "pre_orders": 0,
            "pre_sales": 0, "pre_ad_spend": 0, "pre_new_cx": 0,
            "post_impressions": 0, "post_clicks": 0, "post_orders": 0,
            "post_sales": 0, "post_ad_spend": 0, "post_new_cx": 0,
        },
        "promos": {
            "pre_orders": 0, "pre_sales": 0, "pre_dd_funded": 0, "pre_mx_funded": 0, "pre_new_cx": 0,
            "post_orders": 0, "post_sales": 0, "post_dd_funded": 0, "post_mx_funded": 0, "post_new_cx": 0,
        },
        "totals": {"pre_orders": 0, "pre_gov": 0, "post_orders": 0, "post_gov": 0},
    }

    # Per-mx lift % collections for unweighted averages (used as secondary view).
    unweighted = {
        "channels": {},  # channel -> {gov_lifts: [...], orders_lifts: [...]}
    }

    for rec in per_mx_records:
        # Channels pre/post
        for ch, e in rec["channels_pre_post"].items():
            c = sums["channels"].setdefault(ch, {
                "pre_orders": 0, "pre_gov": 0, "post_orders": 0, "post_gov": 0,
                "count_present": 0, "count_with_pre": 0,
            })
            c["pre_orders"] += e["pre_orders"]
            c["pre_gov"] += e["pre_subtotal"]
            c["post_orders"] += e["post_orders"]
            c["post_gov"] += e["post_subtotal"]
            if e["pre_orders"] > 0 or e["post_orders"] > 0:
                c["count_present"] += 1
            if e["pre_orders"] > 0:
                c["count_with_pre"] += 1
            u = unweighted["channels"].setdefault(ch, {"gov_lifts": [], "orders_lifts": []})
            if e["gov_lift_pct"] is not None:
                u["gov_lifts"].append(e["gov_lift_pct"])
            if e["orders_lift_pct"] is not None:
                u["orders_lifts"].append(e["orders_lift_pct"])

        # Maturation
        for ch, e in rec["channels_maturation"].items():
            c = sums["channels_maturation"].setdefault(ch, {
                "m1_3_orders": 0, "m1_3_subtotal": 0,
                "m4_6_orders": 0, "m4_6_subtotal": 0,
                "latest_3m_orders": 0, "latest_3m_subtotal": 0,
                "count_with_latest": 0,
            })
            c["m1_3_orders"] += e["m1_3_orders"]
            c["m1_3_subtotal"] += e["m1_3_subtotal"]
            c["m4_6_orders"] += e["m4_6_orders"]
            c["m4_6_subtotal"] += e["m4_6_subtotal"]
            c["latest_3m_orders"] += e["latest_3m_orders"]
            c["latest_3m_subtotal"] += e["latest_3m_subtotal"]
            if e["latest_3m_orders"] > 0:
                c["count_with_latest"] += 1

        # MP ops
        ops = rec["mp_ops"]
        sums["mp_ops"]["pre_completed_orders"] += ops["pre_completed_orders"]
        sums["mp_ops"]["pre_cancelled"] += ops["pre_cancelled"]
        sums["mp_ops"]["pre_errors"] += ops["pre_errors"]
        sums["mp_ops"]["post_completed_orders"] += ops["post_completed_orders"]
        sums["mp_ops"]["post_cancelled"] += ops["post_cancelled"]
        sums["mp_ops"]["post_errors"] += ops["post_errors"]
        if ops["pre_avoidable_wait_minutes"]:
            sums["mp_ops"]["pre_wait_total"] += ops["pre_avoidable_wait_minutes"] * ops["pre_completed_orders"]
            sums["mp_ops"]["pre_wait_n"] += ops["pre_completed_orders"]
        if ops["post_avoidable_wait_minutes"]:
            sums["mp_ops"]["post_wait_total"] += ops["post_avoidable_wait_minutes"] * ops["post_completed_orders"]
            sums["mp_ops"]["post_wait_n"] += ops["post_completed_orders"]
        if ops["pre_avg_rating"]:
            sums["mp_ops"]["pre_rating_total"] += ops["pre_avg_rating"] * ops["pre_completed_orders"]
            sums["mp_ops"]["pre_rating_n"] += ops["pre_completed_orders"]
        if ops["post_avg_rating"]:
            sums["mp_ops"]["post_rating_total"] += ops["post_avg_rating"] * ops["post_completed_orders"]
            sums["mp_ops"]["post_rating_n"] += ops["post_completed_orders"]

        # Customers
        for cxt in ("new", "repeat"):
            t = rec["customers"]["total"][cxt]
            sums["customers"][cxt]["pre_orders"] += t["pre_orders"]
            sums["customers"][cxt]["pre_subtotal"] += t["pre_subtotal"]
            sums["customers"][cxt]["post_orders"] += t["post_orders"]
            sums["customers"][cxt]["post_subtotal"] += t["post_subtotal"]

        # SL
        sl = rec["sponsored_listings"]
        for k in ("pre_impressions", "pre_clicks", "pre_orders", "pre_sales", "pre_ad_spend",
                  "pre_new_cx", "post_impressions", "post_clicks", "post_orders",
                  "post_sales", "post_ad_spend", "post_new_cx"):
            sums["sl"][k] += sl[k]

        # Promos
        p = rec["promos"]
        sums["promos"]["pre_orders"] += p["pre_orders"]
        sums["promos"]["pre_sales"] += p["pre_sales"]
        sums["promos"]["pre_dd_funded"] += p["pre_dd_funded_discount"]
        sums["promos"]["pre_mx_funded"] += p["pre_mx_funded_discount"]
        sums["promos"]["pre_new_cx"] += p["pre_new_cx"]
        sums["promos"]["post_orders"] += p["post_orders"]
        sums["promos"]["post_sales"] += p["post_sales"]
        sums["promos"]["post_dd_funded"] += p["post_dd_funded_discount"]
        sums["promos"]["post_mx_funded"] += p["post_mx_funded_discount"]
        sums["promos"]["post_new_cx"] += p["post_new_cx"]

        # Totals
        t = rec["totals_pre_post"]
        sums["totals"]["pre_orders"] += t["pre_orders"]
        sums["totals"]["pre_gov"] += t["pre_gov"]
        sums["totals"]["post_orders"] += t["post_orders"]
        sums["totals"]["post_gov"] += t["post_gov"]

    # ---- Derive cohort-level lifts ----
    cohort = {}

    # Channels (weighted = sum-then-compare; unweighted = mean of per-mx lifts)
    cohort["channels"] = {}
    for ch, c in sums["channels"].items():
        gov_lift_weighted = pct_change(c["post_gov"], c["pre_gov"])
        orders_lift_weighted = pct_change(c["post_orders"], c["pre_orders"])
        u = unweighted["channels"].get(ch, {"gov_lifts": [], "orders_lifts": []})
        gov_lifts = u["gov_lifts"]
        orders_lifts = u["orders_lifts"]
        cohort["channels"][ch] = {
            **c,
            "pre_aov": (c["pre_gov"] / c["pre_orders"]) if c["pre_orders"] else 0,
            "post_aov": (c["post_gov"] / c["post_orders"]) if c["post_orders"] else 0,
            "gov_lift_pct_weighted": gov_lift_weighted,
            "orders_lift_pct_weighted": orders_lift_weighted,
            "gov_lift_pct_unweighted": (sum(gov_lifts) / len(gov_lifts)) if gov_lifts else None,
            "orders_lift_pct_unweighted": (sum(orders_lifts) / len(orders_lifts)) if orders_lifts else None,
            "n_mx_with_pre_data": c["count_with_pre"],
        }

    # Maturation
    cohort["channels_maturation"] = {}
    for ch, c in sums["channels_maturation"].items():
        cohort["channels_maturation"][ch] = {
            **c,
            "m1_3_aov": (c["m1_3_subtotal"] / c["m1_3_orders"]) if c["m1_3_orders"] else 0,
            "m4_6_aov": (c["m4_6_subtotal"] / c["m4_6_orders"]) if c["m4_6_orders"] else 0,
            "latest_aov": (c["latest_3m_subtotal"] / c["latest_3m_orders"]) if c["latest_3m_orders"] else 0,
            "m4_6_vs_m1_3_orders_pct": pct_change(c["m4_6_orders"], c["m1_3_orders"]),
            "m4_6_vs_m1_3_gov_pct": pct_change(c["m4_6_subtotal"], c["m1_3_subtotal"]),
            "latest_vs_m1_3_orders_pct": pct_change(c["latest_3m_orders"], c["m1_3_orders"]) if c["latest_3m_orders"] > 0 else None,
            "latest_vs_m1_3_gov_pct": pct_change(c["latest_3m_subtotal"], c["m1_3_subtotal"]) if c["latest_3m_subtotal"] > 0 else None,
        }

    # MP ops
    o = sums["mp_ops"]
    pre_attempted = o["pre_completed_orders"] + o["pre_cancelled"]
    post_attempted = o["post_completed_orders"] + o["post_cancelled"]
    cohort["mp_ops"] = {
        **o,
        "pre_attempted": pre_attempted,
        "post_attempted": post_attempted,
        # Cancel rate = cancellations / total attempted (completed + cancelled)
        "pre_cancel_rate": (o["pre_cancelled"] / pre_attempted) if pre_attempted else 0,
        "post_cancel_rate": (o["post_cancelled"] / post_attempted) if post_attempted else 0,
        # Error rate = errors / completed orders (errors only defined on completed)
        "pre_error_rate": (o["pre_errors"] / o["pre_completed_orders"]) if o["pre_completed_orders"] else 0,
        "post_error_rate": (o["post_errors"] / o["post_completed_orders"]) if o["post_completed_orders"] else 0,
        "pre_wait_minutes": (o["pre_wait_total"] / o["pre_wait_n"]) if o["pre_wait_n"] else 0,
        "post_wait_minutes": (o["post_wait_total"] / o["post_wait_n"]) if o["post_wait_n"] else 0,
        "pre_avg_rating": (o["pre_rating_total"] / o["pre_rating_n"]) if o["pre_rating_n"] else 0,
        "post_avg_rating": (o["post_rating_total"] / o["post_rating_n"]) if o["post_rating_n"] else 0,
    }
    cohort["mp_ops"]["orders_lift_pct"] = pct_change(o["post_completed_orders"], o["pre_completed_orders"])
    cohort["mp_ops"]["attempted_lift_pct"] = pct_change(post_attempted, pre_attempted)
    # Aliases for back-compat
    cohort["mp_ops"]["pre_orders"] = o["pre_completed_orders"]
    cohort["mp_ops"]["post_orders"] = o["post_completed_orders"]

    # Customers
    cohort["customers"] = {}
    for cxt in ("new", "repeat"):
        c = sums["customers"][cxt]
        cohort["customers"][cxt] = {
            **c,
            "orders_lift_pct": pct_change(c["post_orders"], c["pre_orders"]),
            "gov_lift_pct": pct_change(c["post_subtotal"], c["pre_subtotal"]),
        }

    # SL
    s = sums["sl"]
    cohort["sponsored_listings"] = {
        **s,
        "pre_roas": (s["pre_sales"] / s["pre_ad_spend"]) if s["pre_ad_spend"] else 0,
        "post_roas": (s["post_sales"] / s["post_ad_spend"]) if s["post_ad_spend"] else 0,
        "pre_ctr": (s["pre_clicks"] / s["pre_impressions"]) if s["pre_impressions"] else 0,
        "post_ctr": (s["post_clicks"] / s["post_impressions"]) if s["post_impressions"] else 0,
        "ad_spend_lift_pct": pct_change(s["post_ad_spend"], s["pre_ad_spend"]),
        "sales_lift_pct": pct_change(s["post_sales"], s["pre_sales"]),
        "new_cx_lift_pct": pct_change(s["post_new_cx"], s["pre_new_cx"]),
        "orders_lift_pct": pct_change(s["post_orders"], s["pre_orders"]),
    }

    # Promos
    p = sums["promos"]
    cohort["promos"] = {
        **p,
        "sales_lift_pct": pct_change(p["post_sales"], p["pre_sales"]),
        "new_cx_lift_pct": pct_change(p["post_new_cx"], p["pre_new_cx"]),
    }

    # Totals
    t = sums["totals"]
    cohort["totals"] = {
        **t,
        "orders_lift_pct": pct_change(t["post_orders"], t["pre_orders"]),
        "gov_lift_pct": pct_change(t["post_gov"], t["pre_gov"]),
    }

    # Pathfinder POS rollup at cohort level (In-store + Kiosk combined).
    instore = cohort["channels"].get("In-store", {})
    kiosk = cohort["channels"].get("Kiosk", {})
    mat_instore = cohort["channels_maturation"].get("In-store", {})
    mat_kiosk = cohort["channels_maturation"].get("Kiosk", {})

    pos_pre_orders = instore.get("pre_orders", 0) + kiosk.get("pre_orders", 0)
    pos_pre_gov = instore.get("pre_gov", 0) + kiosk.get("pre_gov", 0)
    pos_post_orders = instore.get("post_orders", 0) + kiosk.get("post_orders", 0)
    pos_post_gov = instore.get("post_gov", 0) + kiosk.get("post_gov", 0)

    mat_m1_3_orders = mat_instore.get("m1_3_orders", 0) + mat_kiosk.get("m1_3_orders", 0)
    mat_m1_3_gov = mat_instore.get("m1_3_subtotal", 0) + mat_kiosk.get("m1_3_subtotal", 0)
    mat_m4_6_orders = mat_instore.get("m4_6_orders", 0) + mat_kiosk.get("m4_6_orders", 0)
    mat_m4_6_gov = mat_instore.get("m4_6_subtotal", 0) + mat_kiosk.get("m4_6_subtotal", 0)
    mat_latest_orders = mat_instore.get("latest_3m_orders", 0) + mat_kiosk.get("latest_3m_orders", 0)
    mat_latest_gov = mat_instore.get("latest_3m_subtotal", 0) + mat_kiosk.get("latest_3m_subtotal", 0)

    cohort["pathfinder_pos"] = {
        "pre_orders": pos_pre_orders,
        "pre_gov": pos_pre_gov,
        "post_orders": pos_post_orders,
        "post_gov": pos_post_gov,
        "orders_lift_pct": pct_change(pos_post_orders, pos_pre_orders),
        "gov_lift_pct": pct_change(pos_post_gov, pos_pre_gov),
        "maturation": {
            "m1_3_orders": mat_m1_3_orders,
            "m1_3_gov": mat_m1_3_gov,
            "m4_6_orders": mat_m4_6_orders,
            "m4_6_gov": mat_m4_6_gov,
            "latest_3m_orders": mat_latest_orders,
            "latest_3m_gov": mat_latest_gov,
            "m4_6_vs_m1_3_orders_pct": pct_change(mat_m4_6_orders, mat_m1_3_orders),
            "m4_6_vs_m1_3_gov_pct": pct_change(mat_m4_6_gov, mat_m1_3_gov),
            "latest_vs_m1_3_orders_pct": pct_change(mat_latest_orders, mat_m1_3_orders) if mat_latest_orders > 0 else None,
            "latest_vs_m1_3_gov_pct": pct_change(mat_latest_gov, mat_m1_3_gov) if mat_latest_gov > 0 else None,
        },
    }

    return cohort


def main():
    raw_files = sorted(RAW_DIR.glob("*.json"))
    if not raw_files:
        print(f"No raw files found in {RAW_DIR}.")
        return

    per_mx = []
    for f in raw_files:
        raw = json.loads(f.read_text())
        per_mx.append(parse_per_mx(raw))

    cohort = cohort_aggregate(per_mx)

    out = {
        "n_mx": len(per_mx),
        "store_ids": [r["store_id"] for r in per_mx],
        "per_mx": per_mx,
        "cohort": cohort,
    }

    out_path = DATA_DIR / "cohort_aggregate.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"Wrote {out_path}")

    # Print a quick summary
    print(f"\nCohort: n={out['n_mx']}")
    print(f"Total pre GOV:  ${cohort['totals']['pre_gov']:>12,.0f}")
    print(f"Total post GOV: ${cohort['totals']['post_gov']:>12,.0f}")
    lift = cohort['totals']['gov_lift_pct']
    print(f"Total GOV lift: {lift*100:>+.1f}%" if lift is not None else "Total GOV lift: undefined")
    print()
    print("Channel pre/post GOV (cohort-weighted):")
    for ch, c in sorted(cohort["channels"].items()):
        lift = c["gov_lift_pct_weighted"]
        lift_str = f"{lift*100:+6.1f}%" if lift is not None else "  (new)"
        print(f"  {ch:<15} pre=${c['pre_gov']:>11,.0f}  post=${c['post_gov']:>11,.0f}  lift={lift_str}  (n_with_pre={c['n_mx_with_pre_data']})")


if __name__ == "__main__":
    main()
