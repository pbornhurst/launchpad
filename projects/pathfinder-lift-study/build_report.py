#!/usr/bin/env python3
"""
Pathfinder Lift Study — Phase 4: report generation.

Reads data/cohort_aggregate.json and renders:
  output/pathfinder-lift-study.html — formatted HTML ready for import to Google Doc
  output/pathfinder-lift-study.md   — markdown copy

Usage:
  python3 build_report.py
  python3 build_report.py --sanitize     # replace mx names with Restaurant A/B/...
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def fmt_money(v, dp=0):
    if v is None or v == "":
        return "—"
    try:
        n = float(v)
    except (TypeError, ValueError):
        return "—"
    if dp == 0:
        return f"${n:,.0f}"
    return f"${n:,.{dp}f}"


def fmt_int(v):
    if v is None:
        return "—"
    try:
        return f"{int(v):,}"
    except (TypeError, ValueError):
        return "—"


def fmt_pct(v, dp=1):
    """Format a fractional lift as a signed percentage with optional 'new' label."""
    if v is None:
        return '<span style="color:#1565C0;">new channel</span>'
    try:
        p = float(v) * 100
    except (TypeError, ValueError):
        return "—"
    color = "#2E7D32" if p > 0 else ("#D63B2F" if p < 0 else "#666")
    sign = "+" if p > 0 else ""
    return f'<b style="color:{color};">{sign}{p:.{dp}f}%</b>'


def fmt_rate(v, dp=2):
    if v is None:
        return "—"
    try:
        return f"{float(v)*100:.{dp}f}%"
    except (TypeError, ValueError):
        return "—"


def fmt_delta_rate(post, pre, dp=2):
    """Show post rate with delta in pp from pre."""
    if post is None or pre is None:
        return "—"
    try:
        pp = (float(post) - float(pre)) * 100
        color = "#2E7D32" if pp < 0 else ("#D63B2F" if pp > 0 else "#666")
        sign = "+" if pp > 0 else ""
        return f'{fmt_rate(post, dp)} <span style="color:{color};font-size:90%;">({sign}{pp:.{dp}f} pp)</span>'
    except (TypeError, ValueError):
        return "—"


def fmt_minutes(v, dp=2):
    if v is None or v == 0:
        return "—"
    try:
        return f"{float(v):.{dp}f} min"
    except (TypeError, ValueError):
        return "—"


def fmt_rating(v):
    if v is None or v == 0:
        return "—"
    try:
        return f"{float(v):.2f}"
    except (TypeError, ValueError):
        return "—"


CSS = """
<style>
  body { font-family: Arial, sans-serif; color: #333; max-width: 980px; margin: 24px auto; line-height: 1.5; }
  h1 { color: #2C3E50; font-size: 28px; margin-bottom: 4px; }
  h2 { color: #2C3E50; font-size: 20px; margin-top: 36px; border-bottom: 2px solid #2C3E50; padding-bottom: 6px; }
  h3 { color: #34495E; font-size: 16px; margin-top: 24px; }
  h4 { color: #34495E; font-size: 14px; margin-top: 18px; margin-bottom: 6px; }
  table { border-collapse: collapse; width: 100%; margin: 12px 0 18px; font-size: 13px; }
  th { background-color: #2C3E50; color: white; padding: 8px 10px; text-align: left; font-weight: 600; }
  td { padding: 7px 10px; border-bottom: 1px solid #e5e5e5; }
  tr:nth-child(even) td { background-color: #f9f9f9; }
  td.num, th.num { text-align: right; }
  .callout { background-color: #f4f6f8; border-left: 4px solid #2C3E50; padding: 12px 16px; margin: 16px 0; font-size: 13px; }
  .hero td { font-size: 14px; }
  .hero td.num b { font-size: 15px; }
  .meta-table td { padding: 4px 12px; }
  .footer { color: #999; font-size: 11px; text-align: center; margin-top: 48px; border-top: 1px solid #ddd; padding-top: 12px; }
  .mini-page { page-break-before: always; margin-top: 40px; border-top: 3px solid #2C3E50; padding-top: 12px; }
  .mini-page h3 { margin-top: 4px; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 3px; font-size: 11px; font-weight: 600; margin-right: 6px; color: white; }
  .badge-info { background-color: #1565C0; }
  .badge-warn { background-color: #E65100; }
  .badge-managed { background-color: #2C3E50; }
  .badge-unmanaged { background-color: #757575; }
</style>
"""


def section_title_methodology(cohort_meta):
    n = cohort_meta["n_mx"]
    today = date.today().isoformat()
    html = f"""
    <h1>Pathfinder Lift Study</h1>
    <p style="color:#666;font-size:14px;margin-top:0;">
      Cohort: {n} merchants live on Pathfinder POS &ge; 6 months, lifetime in-store
      OSW &ge; 300. Prepared {today} for executive review by Pathfinder Strategy &amp; Operations.
    </p>

    <div class="callout">
      <b>Methodology.</b> For each merchant, two comparison windows:
      <ul style="margin:6px 0;">
        <li><b>Marketplace and 1p (Storefront): 6 months pre-install vs 6 months post-install.</b>
        Pathfinder did not exist in the pre-period, so any change reflects how the POS
        affected the merchant's existing DoorDash channels.</li>
        <li><b>In-store and Kiosk: months 1-3 vs months 4-6 on Pathfinder</b>
        (with an additional "latest 3M" column for merchants live &gt; 9 months).
        Pre-install in-store data does not exist by definition &mdash; Pathfinder is the
        in-store POS.</li>
      </ul>
      <b>Caveats.</b> n=10 is descriptive, not causal. Seasonality is not controlled.
      Storefront frequently launches alongside Pathfinder, so a 1p &ldquo;lift&rdquo; often
      reflects a newly-enabled channel rather than a true growth comparison.
      GOV is computed from <code>fact_merchant_orders_portal.subtotal</code>; marketing
      figures from the SL/Promo campaign performance tables.
    </div>
    """
    return html


def section_executive_summary(cohort, n_mx):
    t = cohort["totals"]
    mp = cohort["channels"].get("Marketplace", {})
    sf = cohort["channels"].get("Storefront", {})
    pos = cohort["pathfinder_pos"]
    pos_mat = pos["maturation"]
    sl = cohort["sponsored_listings"]
    cust_new = cohort["customers"]["new"]

    rows = [
        ("Total business GOV (6M pre vs post)", fmt_money(t["pre_gov"]), fmt_money(t["post_gov"]), fmt_pct(t["gov_lift_pct"])),
        ("Marketplace GOV", fmt_money(mp.get("pre_gov", 0)), fmt_money(mp.get("post_gov", 0)), fmt_pct(mp.get("gov_lift_pct_weighted"))),
        ("Marketplace orders", fmt_int(mp.get("pre_orders", 0)), fmt_int(mp.get("post_orders", 0)), fmt_pct(mp.get("orders_lift_pct_weighted"))),
        ("New customers acquired (MP+1p)", fmt_int(cust_new["pre_orders"]), fmt_int(cust_new["post_orders"]), fmt_pct(cust_new["orders_lift_pct"])),
        ("Storefront (1p) GOV", fmt_money(sf.get("pre_gov", 0)), fmt_money(sf.get("post_gov", 0)), fmt_pct(sf.get("gov_lift_pct_weighted"))),
        ("Sponsored Listings ROAS", f"{sl['pre_roas']:.2f}x", f"{sl['post_roas']:.2f}x", fmt_pct((sl['post_roas']/sl['pre_roas'] - 1) if sl['pre_roas'] else None)),
        ("Pathfinder POS GOV (M4-6 vs M1-3 ramp)", fmt_money(pos_mat["m1_3_gov"]), fmt_money(pos_mat["m4_6_gov"]), fmt_pct(pos_mat["m4_6_vs_m1_3_gov_pct"])),
        ("Pathfinder POS GOV (cumulative 6M post-install)", "—", fmt_money(pos["post_gov"]), '<span style="color:#1565C0;">enabled by POS</span>'),
    ]
    table_rows = "".join(
        f'<tr><td>{r[0]}</td><td class="num">{r[1]}</td><td class="num">{r[2]}</td><td class="num">{r[3]}</td></tr>'
        for r in rows
    )

    return f"""
    <h2>Executive Summary</h2>
    <p>Across {n_mx} merchants drawn from a 121-mx eligible pool (&ge;6M live, &ge;300 OSW),
    Pathfinder POS coincides with measurable lifts in the existing DoorDash channels
    (Marketplace, Storefront) and a clean in-store maturation curve through the
    first 6 months.</p>
    <table class="hero">
      <thead><tr><th>Hero metric</th><th class="num">Pre / Months 1-3</th><th class="num">Post / Months 4-6</th><th class="num">&Delta;</th></tr></thead>
      <tbody>{table_rows}</tbody>
    </table>
    """


def section_cohort_composition(per_mx, sanitize=False):
    rows_html = []
    for i, r in enumerate(per_mx, 1):
        m = r["metadata"]
        name = f"Restaurant {chr(64+i)}" if sanitize else r.get("store_name") or "—"
        tenure = (date.today() - date.fromisoformat(r["windows"]["post_start"])).days
        mgmt = m.get("management_type_grouped") or "—"
        badge = "managed" if "MANAGED" in (mgmt or "") and "UNMANAGED" not in (mgmt or "") else "unmanaged"
        badge_html = f'<span class="badge badge-{badge}">{mgmt.title()}</span>'
        rows_html.append(
            f'<tr>'
            f'<td class="num">{i}</td>'
            f'<td>{name}</td>'
            f'<td>{m.get("cuisine_bucket") or "Other"}</td>'
            f'<td>{m.get("region_bucket") or "—"}</td>'
            f'<td>{badge_html}</td>'
            f'<td>{r["install_date"]}</td>'
            f'<td class="num">{tenure} d</td>'
            f'<td class="num">{float(m.get("lifetime_osw") or 0):,.0f}</td>'
            f'<td class="num">{fmt_money(float(m.get("lifetime_gov_store_week") or 0))}</td>'
            f'</tr>'
        )
    return f"""
    <h2>Cohort Composition</h2>
    <p>Selected by greedy diversification across cuisine, region, and management
    type (Managed vs Unmanaged SMB), with a soft cap on per-region count to
    avoid skew toward the heavier-weighted West coast.</p>
    <table>
      <thead><tr>
        <th class="num">#</th><th>Merchant</th><th>Cuisine</th><th>Region</th>
        <th>Mgmt</th><th>Install</th><th class="num">Tenure</th>
        <th class="num">Lifetime OSW</th><th class="num">Lifetime GOV/wk</th>
      </tr></thead>
      <tbody>{"".join(rows_html)}</tbody>
    </table>
    """


def section_existing_channel_lift(cohort, per_mx, sanitize=False):
    """MP + Storefront pre/post (6M vs 6M)."""
    parts = ['<h2>Existing-Channel Lift &mdash; 6M Pre vs 6M Post Install</h2>']
    parts.append("<p>For the two DoorDash channels that existed before Pathfinder install &mdash; Marketplace and Storefront (1p) &mdash; we compare the 180-day window immediately preceding the install date against the 180 days following. Storefront frequently launches with Pathfinder, so 1p lifts often reflect newly-enabled volume rather than growth on an existing base.</p>")

    for channel in ("Marketplace", "Storefront"):
        c = cohort["channels"].get(channel)
        if not c:
            continue
        parts.append(f'<h3>{channel}</h3>')
        cohort_row = (
            f'<tr><td><b>Cohort total (n={c["count_present"]})</b></td>'
            f'<td class="num">{fmt_int(c["pre_orders"])}</td>'
            f'<td class="num">{fmt_int(c["post_orders"])}</td>'
            f'<td class="num">{fmt_pct(c["orders_lift_pct_weighted"])}</td>'
            f'<td class="num">{fmt_money(c["pre_gov"])}</td>'
            f'<td class="num">{fmt_money(c["post_gov"])}</td>'
            f'<td class="num">{fmt_pct(c["gov_lift_pct_weighted"])}</td>'
            f'<td class="num">{fmt_money(c["pre_aov"], dp=2)}</td>'
            f'<td class="num">{fmt_money(c["post_aov"], dp=2)}</td></tr>'
        )
        rows = [cohort_row]
        for i, r in enumerate(per_mx, 1):
            name = f"Restaurant {chr(64+i)}" if sanitize else r.get("store_name") or "—"
            ch = r["channels_pre_post"].get(channel)
            if not ch:
                rows.append(f'<tr><td>{name}</td><td colspan="8" style="color:#999;">no data</td></tr>')
                continue
            rows.append(
                f'<tr><td>{name}</td>'
                f'<td class="num">{fmt_int(ch["pre_orders"])}</td>'
                f'<td class="num">{fmt_int(ch["post_orders"])}</td>'
                f'<td class="num">{fmt_pct(ch["orders_lift_pct"])}</td>'
                f'<td class="num">{fmt_money(ch["pre_subtotal"])}</td>'
                f'<td class="num">{fmt_money(ch["post_subtotal"])}</td>'
                f'<td class="num">{fmt_pct(ch["gov_lift_pct"])}</td>'
                f'<td class="num">{fmt_money(ch["pre_aov"], dp=2)}</td>'
                f'<td class="num">{fmt_money(ch["post_aov"], dp=2)}</td></tr>'
            )
        parts.append(
            '<table><thead><tr>'
            '<th>Merchant</th>'
            '<th class="num">Pre orders</th><th class="num">Post orders</th><th class="num">&Delta;</th>'
            '<th class="num">Pre GOV</th><th class="num">Post GOV</th><th class="num">&Delta;</th>'
            '<th class="num">Pre AOV</th><th class="num">Post AOV</th>'
            '</tr></thead><tbody>' + "".join(rows) + '</tbody></table>'
        )
    return "".join(parts)


def section_operations(cohort, per_mx, sanitize=False):
    o = cohort["mp_ops"]
    rows = [
        f'<tr><td><b>Cohort (Marketplace only)</b></td>'
        f'<td class="num">{fmt_int(o["pre_completed_orders"])}</td>'
        f'<td class="num">{fmt_int(o["post_completed_orders"])}</td>'
        f'<td class="num">{fmt_delta_rate(o["post_cancel_rate"], o["pre_cancel_rate"])}</td>'
        f'<td class="num">{fmt_delta_rate(o["post_error_rate"], o["pre_error_rate"])}</td>'
        f'<td class="num">{fmt_minutes(o["pre_wait_minutes"])} &rarr; {fmt_minutes(o["post_wait_minutes"])}</td>'
        f'<td class="num">{fmt_rating(o["pre_avg_rating"])} &rarr; {fmt_rating(o["post_avg_rating"])}</td></tr>'
    ]
    for i, r in enumerate(per_mx, 1):
        name = f"Restaurant {chr(64+i)}" if sanitize else r.get("store_name") or "—"
        op = r["mp_ops"]
        rows.append(
            f'<tr><td>{name}</td>'
            f'<td class="num">{fmt_int(op["pre_completed_orders"])}</td>'
            f'<td class="num">{fmt_int(op["post_completed_orders"])}</td>'
            f'<td class="num">{fmt_delta_rate(op["post_cancel_rate"], op["pre_cancel_rate"])}</td>'
            f'<td class="num">{fmt_delta_rate(op["post_error_rate"], op["pre_error_rate"])}</td>'
            f'<td class="num">{fmt_minutes(op["pre_wait_minutes"])} &rarr; {fmt_minutes(op["post_wait_minutes"])}</td>'
            f'<td class="num">{fmt_rating(op["pre_avg_rating"])} &rarr; {fmt_rating(op["post_avg_rating"])}</td></tr>'
        )
    return f"""
    <h2>Marketplace Operations &mdash; 6M Pre vs 6M Post</h2>
    <p>Delivery quality on completed Marketplace orders. Order counts are completed orders only. Cancellation rate
    = cancelled attempts divided by total attempts (completed + cancelled). Error rate = missing/incorrect orders
    divided by completed orders. Lower cancellation and error rates are improvements; lower wait minutes is better.</p>
    <table><thead><tr>
      <th>Merchant</th>
      <th class="num">Pre MP orders (completed)</th><th class="num">Post MP orders (completed)</th>
      <th class="num">Cancel rate</th><th class="num">Error rate</th>
      <th class="num">Avoidable wait</th><th class="num">Mx rating</th>
    </tr></thead><tbody>{"".join(rows)}</tbody></table>
    """


def section_customer_acquisition(cohort, per_mx, sanitize=False):
    new = cohort["customers"]["new"]
    rep = cohort["customers"]["repeat"]
    return f"""
    <h2>Customer Acquisition &mdash; 6M Pre vs 6M Post</h2>
    <p>Counts of new and repeat customers from Marketplace and Storefront orders combined,
    based on <code>cx_type_within_store</code>.</p>
    <table><thead><tr>
      <th>Customer type</th>
      <th class="num">Pre orders</th><th class="num">Post orders</th><th class="num">&Delta;</th>
      <th class="num">Pre GOV</th><th class="num">Post GOV</th><th class="num">&Delta;</th>
    </tr></thead><tbody>
      <tr><td><b>New customers</b></td>
        <td class="num">{fmt_int(new["pre_orders"])}</td><td class="num">{fmt_int(new["post_orders"])}</td><td class="num">{fmt_pct(new["orders_lift_pct"])}</td>
        <td class="num">{fmt_money(new["pre_subtotal"])}</td><td class="num">{fmt_money(new["post_subtotal"])}</td><td class="num">{fmt_pct(new["gov_lift_pct"])}</td>
      </tr>
      <tr><td><b>Repeat customers</b></td>
        <td class="num">{fmt_int(rep["pre_orders"])}</td><td class="num">{fmt_int(rep["post_orders"])}</td><td class="num">{fmt_pct(rep["orders_lift_pct"])}</td>
        <td class="num">{fmt_money(rep["pre_subtotal"])}</td><td class="num">{fmt_money(rep["post_subtotal"])}</td><td class="num">{fmt_pct(rep["gov_lift_pct"])}</td>
      </tr>
    </tbody></table>
    """


def section_marketing(cohort):
    sl = cohort["sponsored_listings"]
    pr = cohort["promos"]
    return f"""
    <h2>Marketing Efficiency &mdash; 6M Pre vs 6M Post</h2>
    <h3>Sponsored Listings</h3>
    <table><thead><tr>
      <th>Metric</th><th class="num">Pre 6M</th><th class="num">Post 6M</th><th class="num">&Delta;</th>
    </tr></thead><tbody>
      <tr><td>Impressions</td><td class="num">{fmt_int(sl["pre_impressions"])}</td><td class="num">{fmt_int(sl["post_impressions"])}</td><td class="num">{fmt_pct(pct_change(sl["post_impressions"], sl["pre_impressions"]))}</td></tr>
      <tr><td>Clicks</td><td class="num">{fmt_int(sl["pre_clicks"])}</td><td class="num">{fmt_int(sl["post_clicks"])}</td><td class="num">{fmt_pct(pct_change(sl["post_clicks"], sl["pre_clicks"]))}</td></tr>
      <tr><td>Click-through rate</td><td class="num">{fmt_rate(sl["pre_ctr"])}</td><td class="num">{fmt_rate(sl["post_ctr"])}</td><td class="num">{fmt_delta_rate(sl["post_ctr"], sl["pre_ctr"])}</td></tr>
      <tr><td>Attributed orders</td><td class="num">{fmt_int(sl["pre_orders"])}</td><td class="num">{fmt_int(sl["post_orders"])}</td><td class="num">{fmt_pct(sl["orders_lift_pct"])}</td></tr>
      <tr><td>Attributed sales</td><td class="num">{fmt_money(sl["pre_sales"])}</td><td class="num">{fmt_money(sl["post_sales"])}</td><td class="num">{fmt_pct(sl["sales_lift_pct"])}</td></tr>
      <tr><td>Ad spend</td><td class="num">{fmt_money(sl["pre_ad_spend"])}</td><td class="num">{fmt_money(sl["post_ad_spend"])}</td><td class="num">{fmt_pct(sl["ad_spend_lift_pct"])}</td></tr>
      <tr><td><b>ROAS</b></td><td class="num">{sl["pre_roas"]:.2f}x</td><td class="num">{sl["post_roas"]:.2f}x</td><td class="num">{fmt_pct((sl["post_roas"]/sl["pre_roas"]-1) if sl["pre_roas"] else None)}</td></tr>
      <tr><td>New customers acquired via SL</td><td class="num">{fmt_int(sl["pre_new_cx"])}</td><td class="num">{fmt_int(sl["post_new_cx"])}</td><td class="num">{fmt_pct(sl["new_cx_lift_pct"])}</td></tr>
    </tbody></table>
    <h3>Promo Campaigns</h3>
    <table><thead><tr>
      <th>Metric</th><th class="num">Pre 6M</th><th class="num">Post 6M</th><th class="num">&Delta;</th>
    </tr></thead><tbody>
      <tr><td>Promo-attributed orders</td><td class="num">{fmt_int(pr["pre_orders"])}</td><td class="num">{fmt_int(pr["post_orders"])}</td><td class="num">{fmt_pct(pct_change(pr["post_orders"], pr["pre_orders"]))}</td></tr>
      <tr><td>Promo-attributed sales</td><td class="num">{fmt_money(pr["pre_sales"])}</td><td class="num">{fmt_money(pr["post_sales"])}</td><td class="num">{fmt_pct(pr["sales_lift_pct"])}</td></tr>
      <tr><td>DoorDash-funded discount</td><td class="num">{fmt_money(pr["pre_dd_funded"])}</td><td class="num">{fmt_money(pr["post_dd_funded"])}</td><td class="num">{fmt_pct(pct_change(pr["post_dd_funded"], pr["pre_dd_funded"]))}</td></tr>
      <tr><td>Mx-funded discount</td><td class="num">{fmt_money(pr["pre_mx_funded"])}</td><td class="num">{fmt_money(pr["post_mx_funded"])}</td><td class="num">{fmt_pct(pct_change(pr["post_mx_funded"], pr["pre_mx_funded"]))}</td></tr>
      <tr><td>New customers via promo</td><td class="num">{fmt_int(pr["pre_new_cx"])}</td><td class="num">{fmt_int(pr["post_new_cx"])}</td><td class="num">{fmt_pct(pr["new_cx_lift_pct"])}</td></tr>
    </tbody></table>
    """


def pct_change(post, pre):
    if pre is None or float(pre) == 0:
        return None
    return (float(post) - float(pre)) / float(pre)


def section_maturation(cohort, per_mx, sanitize=False):
    parts = ['<h2>Pathfinder POS Maturation &mdash; Months 1-3 vs 4-6</h2>']
    parts.append("<p>For the channels Pathfinder enables (In-store CC and Kiosk), pre-install data does not exist. Instead we compare the merchant's first 90 days on Pathfinder against days 91-180, with an additional &ldquo;latest 3M&rdquo; column for merchants who have been live more than 9 months. This is the maturation curve: does the in-store channel ramp and hold?</p>")
    parts.append("<p>The first table sums In-store + Kiosk into a Pathfinder POS total (the right view for any merchant with kiosk volume). Per-channel breakdowns follow.</p>")

    # Pathfinder POS combined rollup
    pm = cohort["pathfinder_pos"]["maturation"]
    cohort_pos_row = (
        f'<tr><td><b>Cohort total (Pathfinder POS = In-store + Kiosk)</b></td>'
        f'<td class="num">{fmt_int(pm["m1_3_orders"])}</td>'
        f'<td class="num">{fmt_money(pm["m1_3_gov"])}</td>'
        f'<td class="num">{fmt_int(pm["m4_6_orders"])}</td>'
        f'<td class="num">{fmt_money(pm["m4_6_gov"])}</td>'
        f'<td class="num">{fmt_pct(pm["m4_6_vs_m1_3_gov_pct"])}</td>'
        f'<td class="num">{fmt_int(pm["latest_3m_orders"]) if pm["latest_3m_orders"] else "—"}</td>'
        f'<td class="num">{fmt_money(pm["latest_3m_gov"]) if pm["latest_3m_gov"] else "—"}</td>'
        f'<td class="num">{fmt_pct(pm.get("latest_vs_m1_3_gov_pct"))}</td>'
        f'</tr>'
    )
    pos_rows = [cohort_pos_row]
    for i, r in enumerate(per_mx, 1):
        name = f"Restaurant {chr(64+i)}" if sanitize else r.get("store_name") or "—"
        pp = r["pathfinder_pos"]["maturation"]
        if pp.get("m1_3_orders", 0) == 0 and pp.get("m4_6_orders", 0) == 0:
            pos_rows.append(f'<tr><td>{name}</td><td colspan="8" style="color:#999;">no Pathfinder volume in maturation windows</td></tr>')
            continue
        latest_present = pp.get("latest_3m_orders", 0) > 0
        pos_rows.append(
            f'<tr><td>{name}</td>'
            f'<td class="num">{fmt_int(pp["m1_3_orders"])}</td>'
            f'<td class="num">{fmt_money(pp["m1_3_subtotal"])}</td>'
            f'<td class="num">{fmt_int(pp["m4_6_orders"])}</td>'
            f'<td class="num">{fmt_money(pp["m4_6_subtotal"])}</td>'
            f'<td class="num">{fmt_pct(pp.get("m4_6_vs_m1_3_gov_pct"))}</td>'
            f'<td class="num">{fmt_int(pp["latest_3m_orders"]) if latest_present else "—"}</td>'
            f'<td class="num">{fmt_money(pp["latest_3m_subtotal"]) if latest_present else "—"}</td>'
            f'<td class="num">{fmt_pct(pp.get("latest_vs_m1_3_gov_pct")) if latest_present else "—"}</td>'
            f'</tr>'
        )
    parts.append('<h3>Pathfinder POS Total (In-store + Kiosk)</h3>')
    parts.append(
        '<table><thead><tr>'
        '<th>Merchant</th>'
        '<th class="num">M1-3 orders</th><th class="num">M1-3 GOV</th>'
        '<th class="num">M4-6 orders</th><th class="num">M4-6 GOV</th><th class="num">&Delta;</th>'
        '<th class="num">Latest 3M orders</th><th class="num">Latest 3M GOV</th><th class="num">&Delta; vs M1-3</th>'
        '</tr></thead><tbody>' + "".join(pos_rows) + '</tbody></table>'
    )

    for channel in ("In-store", "Kiosk"):
        c = cohort["channels_maturation"].get(channel)
        if not c:
            continue
        parts.append(f'<h3>{channel}</h3>')
        cohort_row = (
            f'<tr><td><b>Cohort total</b></td>'
            f'<td class="num">{fmt_int(c["m1_3_orders"])}</td>'
            f'<td class="num">{fmt_money(c["m1_3_subtotal"])}</td>'
            f'<td class="num">{fmt_int(c["m4_6_orders"])}</td>'
            f'<td class="num">{fmt_money(c["m4_6_subtotal"])}</td>'
            f'<td class="num">{fmt_pct(c["m4_6_vs_m1_3_gov_pct"])}</td>'
            f'<td class="num">{fmt_int(c["latest_3m_orders"]) if c["latest_3m_orders"] else "—"}</td>'
            f'<td class="num">{fmt_money(c["latest_3m_subtotal"]) if c["latest_3m_subtotal"] else "—"}</td>'
            f'<td class="num">{fmt_pct(c.get("latest_vs_m1_3_gov_pct"))}</td>'
            f'</tr>'
        )
        rows = [cohort_row]
        for i, r in enumerate(per_mx, 1):
            name = f"Restaurant {chr(64+i)}" if sanitize else r.get("store_name") or "—"
            ch = r["channels_maturation"].get(channel)
            if not ch or (ch.get("m1_3_orders", 0) == 0 and ch.get("m4_6_orders", 0) == 0):
                rows.append(f'<tr><td>{name}</td><td colspan="8" style="color:#999;">no in-store volume in maturation windows</td></tr>')
                continue
            latest_present = ch.get("latest_3m_orders", 0) > 0
            rows.append(
                f'<tr><td>{name}</td>'
                f'<td class="num">{fmt_int(ch["m1_3_orders"])}</td>'
                f'<td class="num">{fmt_money(ch["m1_3_subtotal"])}</td>'
                f'<td class="num">{fmt_int(ch["m4_6_orders"])}</td>'
                f'<td class="num">{fmt_money(ch["m4_6_subtotal"])}</td>'
                f'<td class="num">{fmt_pct(ch.get("m4_6_vs_m1_3_gov_pct"))}</td>'
                f'<td class="num">{fmt_int(ch["latest_3m_orders"]) if latest_present else "—"}</td>'
                f'<td class="num">{fmt_money(ch["latest_3m_subtotal"]) if latest_present else "—"}</td>'
                f'<td class="num">{fmt_pct(ch.get("latest_vs_m1_3_gov_pct")) if latest_present else "—"}</td>'
                f'</tr>'
            )
        parts.append(
            '<table><thead><tr>'
            '<th>Merchant</th>'
            '<th class="num">M1-3 orders</th><th class="num">M1-3 GOV</th>'
            '<th class="num">M4-6 orders</th><th class="num">M4-6 GOV</th><th class="num">&Delta;</th>'
            '<th class="num">Latest 3M orders</th><th class="num">Latest 3M GOV</th><th class="num">&Delta; vs M1-3</th>'
            '</tr></thead><tbody>' + "".join(rows) + '</tbody></table>'
        )
    return "".join(parts)


def section_appendix_mini(r, i, sanitize=False):
    """One mini one-pager per mx in the appendix."""
    m = r["metadata"]
    name = f"Restaurant {chr(64+i)}" if sanitize else r.get("store_name") or "—"
    tenure = (date.today() - date.fromisoformat(r["windows"]["post_start"])).days
    mgmt = m.get("management_type_grouped") or "—"

    # Hero metrics
    t = r["totals_pre_post"]
    mp = r["channels_pre_post"].get("Marketplace", {})
    sf = r["channels_pre_post"].get("Storefront", {})
    pos = r["pathfinder_pos"]
    pos_mat = pos["maturation"]
    sl = r["sponsored_listings"]
    cust_new = r["customers"]["total"]["new"]

    flags_html = ""
    if r["coverage_flags"]:
        flags_html = '<div class="callout" style="font-size:12px;border-left-color:#E65100;">' \
                     '<b>Coverage notes:</b> ' + ", ".join(r["coverage_flags"]) + '</div>'

    hero_rows = [
        ("Total business GOV (6M pre &rarr; 6M post)", fmt_money(t["pre_gov"]), fmt_money(t["post_gov"]), fmt_pct(t["gov_lift_pct"])),
        ("Marketplace GOV", fmt_money(mp.get("pre_subtotal", 0)), fmt_money(mp.get("post_subtotal", 0)), fmt_pct(mp.get("gov_lift_pct"))),
        ("Storefront GOV", fmt_money(sf.get("pre_subtotal", 0)), fmt_money(sf.get("post_subtotal", 0)), fmt_pct(sf.get("gov_lift_pct"))),
        ("Pathfinder POS GOV (cumulative 6M post)", "—", fmt_money(pos["post_gov"]), '<span style="color:#1565C0;">enabled by POS</span>'),
        ("Pathfinder POS GOV (M1-3 &rarr; M4-6 ramp)", fmt_money(pos_mat["m1_3_subtotal"]), fmt_money(pos_mat["m4_6_subtotal"]), fmt_pct(pos_mat["m4_6_vs_m1_3_gov_pct"])),
        ("New customers (MP+1p)", fmt_int(cust_new["pre_orders"]), fmt_int(cust_new["post_orders"]), fmt_pct(cust_new["orders_lift_pct"])),
        ("Sponsored Listings ROAS", f"{sl['pre_roas']:.2f}x" if sl['pre_roas'] else "—", f"{sl['post_roas']:.2f}x" if sl['post_roas'] else "—", fmt_pct((sl['post_roas']/sl['pre_roas'] - 1) if sl['pre_roas'] else None)),
    ]
    hero_rows_html = "".join(
        f'<tr><td>{row[0]}</td><td class="num">{row[1]}</td><td class="num">{row[2]}</td><td class="num">{row[3]}</td></tr>'
        for row in hero_rows
    )

    # Channel mix table (orders + GOV for both windows)
    channel_rows = []
    for channel in ("Marketplace", "Storefront", "In-store", "Kiosk"):
        if channel in ("Marketplace", "Storefront"):
            ch = r["channels_pre_post"].get(channel)
            if ch:
                channel_rows.append(
                    f'<tr><td>{channel}</td>'
                    f'<td class="num">6M pre vs post</td>'
                    f'<td class="num">{fmt_int(ch["pre_orders"])}</td>'
                    f'<td class="num">{fmt_int(ch["post_orders"])}</td>'
                    f'<td class="num">{fmt_pct(ch["orders_lift_pct"])}</td>'
                    f'<td class="num">{fmt_money(ch["pre_subtotal"])}</td>'
                    f'<td class="num">{fmt_money(ch["post_subtotal"])}</td>'
                    f'<td class="num">{fmt_pct(ch["gov_lift_pct"])}</td></tr>'
                )
        else:
            ch = r["channels_maturation"].get(channel)
            if ch and (ch.get("m1_3_orders", 0) > 0 or ch.get("m4_6_orders", 0) > 0):
                channel_rows.append(
                    f'<tr><td>{channel}</td>'
                    f'<td class="num">M1-3 vs M4-6</td>'
                    f'<td class="num">{fmt_int(ch["m1_3_orders"])}</td>'
                    f'<td class="num">{fmt_int(ch["m4_6_orders"])}</td>'
                    f'<td class="num">{fmt_pct(ch.get("m4_6_vs_m1_3_orders_pct"))}</td>'
                    f'<td class="num">{fmt_money(ch["m1_3_subtotal"])}</td>'
                    f'<td class="num">{fmt_money(ch["m4_6_subtotal"])}</td>'
                    f'<td class="num">{fmt_pct(ch.get("m4_6_vs_m1_3_gov_pct"))}</td></tr>'
                )

    channel_table = ""
    if channel_rows:
        channel_table = (
            '<h4>Channel breakdown</h4>'
            '<table><thead><tr>'
            '<th>Channel</th><th>Comparison</th>'
            '<th class="num">Orders A</th><th class="num">Orders B</th><th class="num">&Delta;</th>'
            '<th class="num">GOV A</th><th class="num">GOV B</th><th class="num">&Delta;</th>'
            '</tr></thead><tbody>' + "".join(channel_rows) + '</tbody></table>'
        )

    # MP ops mini
    op = r["mp_ops"]
    ops_html = ""
    if op["pre_completed_orders"] > 0 or op["post_completed_orders"] > 0:
        ops_html = (
            '<h4>Marketplace operations</h4>'
            '<table><thead><tr><th>Metric</th><th class="num">Pre</th><th class="num">Post</th></tr></thead><tbody>'
            f'<tr><td>Completed MP orders</td><td class="num">{fmt_int(op["pre_completed_orders"])}</td><td class="num">{fmt_int(op["post_completed_orders"])}</td></tr>'
            f'<tr><td>Cancelled MP attempts</td><td class="num">{fmt_int(op["pre_cancelled"])}</td><td class="num">{fmt_int(op["post_cancelled"])}</td></tr>'
            f'<tr><td>Cancellation rate</td><td class="num">{fmt_rate(op["pre_cancel_rate"])}</td><td class="num">{fmt_rate(op["post_cancel_rate"])}</td></tr>'
            f'<tr><td>Error rate</td><td class="num">{fmt_rate(op["pre_error_rate"])}</td><td class="num">{fmt_rate(op["post_error_rate"])}</td></tr>'
            f'<tr><td>Avoidable dasher wait</td><td class="num">{fmt_minutes(op["pre_wait_minutes"])}</td><td class="num">{fmt_minutes(op["post_wait_minutes"])}</td></tr>'
            f'<tr><td>Avg mx rating</td><td class="num">{fmt_rating(op["pre_avg_rating"])}</td><td class="num">{fmt_rating(op["post_avg_rating"])}</td></tr>'
            '</tbody></table>'
        )

    return f"""
    <div class="mini-page">
      <h3>{i}. {name}</h3>
      <table class="meta-table"><tbody>
        <tr><td><b>Cuisine</b></td><td>{m.get("cuisine_type") or "—"}</td>
            <td><b>Region</b></td><td>{m.get("submarket_name") or "—"} ({m.get("region_bucket") or "—"})</td></tr>
        <tr><td><b>Mgmt</b></td><td>{mgmt}</td>
            <td><b>Install</b></td><td>{r["install_date"]} ({tenure} days ago)</td></tr>
        <tr><td><b>Lifetime OSW</b></td><td>{float(m.get("lifetime_osw") or 0):,.0f}</td>
            <td><b>Lifetime GOV/wk</b></td><td>{fmt_money(float(m.get("lifetime_gov_store_week") or 0))}</td></tr>
      </tbody></table>
      {flags_html}
      <h4>Hero metrics</h4>
      <table><thead><tr><th>Metric</th><th class="num">A</th><th class="num">B</th><th class="num">&Delta;</th></tr></thead>
      <tbody>{hero_rows_html}</tbody></table>
      {channel_table}
      {ops_html}
    </div>
    """


def section_footer():
    return f"""
    <div class="footer">
      Generated {date.today().isoformat()} | Pathfinder Account Management |
      n=10 cohort study, descriptive analysis | Source: DoorDash internal data warehouse
    </div>
    """


def render_html(payload, sanitize=False):
    cohort = payload["cohort"]
    per_mx = payload["per_mx"]
    n = payload["n_mx"]

    sections = [
        CSS,
        section_title_methodology({"n_mx": n}),
        section_executive_summary(cohort, n),
        section_cohort_composition(per_mx, sanitize),
        section_existing_channel_lift(cohort, per_mx, sanitize),
        section_operations(cohort, per_mx, sanitize),
        section_customer_acquisition(cohort, per_mx, sanitize),
        section_marketing(cohort),
        section_maturation(cohort, per_mx, sanitize),
        '<h2 style="page-break-before:always;">Appendix &mdash; Per-Merchant Profiles</h2>',
        *(section_appendix_mini(r, i, sanitize) for i, r in enumerate(per_mx, 1)),
        section_footer(),
    ]
    return "<!doctype html><html><head><meta charset=\"utf-8\"><title>Pathfinder Lift Study</title></head><body>" + "".join(sections) + "</body></html>"


def render_markdown(payload):
    """Compact markdown copy for repo / pasting."""
    cohort = payload["cohort"]
    n = payload["n_mx"]
    t = cohort["totals"]
    mp = cohort["channels"].get("Marketplace", {})
    sf = cohort["channels"].get("Storefront", {})
    pos = cohort["pathfinder_pos"]
    pos_mat = pos["maturation"]
    sl = cohort["sponsored_listings"]
    cust_new = cohort["customers"]["new"]

    def pct(v, dp=1):
        if v is None:
            return "(new)"
        return f"{v*100:+.{dp}f}%"

    lines = [
        f"# Pathfinder Lift Study (n={n})",
        f"_Generated {date.today().isoformat()}._",
        "",
        "## Executive Summary",
        "",
        "| Hero metric | Pre / M1-3 | Post / M4-6 | Δ |",
        "|---|---:|---:|---:|",
        f"| Total business GOV | ${t['pre_gov']:,.0f} | ${t['post_gov']:,.0f} | {pct(t['gov_lift_pct'])} |",
        f"| Marketplace GOV | ${mp.get('pre_gov',0):,.0f} | ${mp.get('post_gov',0):,.0f} | {pct(mp.get('gov_lift_pct_weighted'))} |",
        f"| Marketplace orders | {mp.get('pre_orders',0):,} | {mp.get('post_orders',0):,} | {pct(mp.get('orders_lift_pct_weighted'))} |",
        f"| New customers (MP+1p) | {cust_new['pre_orders']:,} | {cust_new['post_orders']:,} | {pct(cust_new['orders_lift_pct'])} |",
        f"| Storefront GOV | ${sf.get('pre_gov',0):,.0f} | ${sf.get('post_gov',0):,.0f} | {pct(sf.get('gov_lift_pct_weighted'))} |",
        f"| SL ROAS | {sl['pre_roas']:.2f}x | {sl['post_roas']:.2f}x | {pct((sl['post_roas']/sl['pre_roas']-1) if sl['pre_roas'] else None)} |",
        f"| Pathfinder POS GOV (M4-6 vs M1-3) | ${pos_mat['m1_3_gov']:,.0f} | ${pos_mat['m4_6_gov']:,.0f} | {pct(pos_mat['m4_6_vs_m1_3_gov_pct'])} |",
        f"| Pathfinder POS GOV (cumulative 6M post) | — | ${pos['post_gov']:,.0f} | enabled by POS |",
    ]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sanitize", action="store_true", help="Replace mx names with Restaurant A/B/...")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = json.loads((DATA_DIR / "cohort_aggregate.json").read_text())

    html = render_html(payload, sanitize=args.sanitize)
    md = render_markdown(payload)

    html_path = OUTPUT_DIR / "pathfinder-lift-study.html"
    md_path = OUTPUT_DIR / "pathfinder-lift-study.md"
    html_path.write_text(html)
    md_path.write_text(md)
    print(f"Wrote {html_path} ({len(html):,} bytes)")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
