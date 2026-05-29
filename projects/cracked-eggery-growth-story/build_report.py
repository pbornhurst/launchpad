#!/usr/bin/env python3
"""
Cracked Eggery growth story - render HTML report.

Reads data/aggregate.json and writes output/cracked-eggery-growth-story.html.
Mirrors the look-and-feel of projects/pathfinder-lift-study/output/pathfinder-lift-study.html
but adapted for n=2 short-tenure cohort.

Usage: python3 build_report.py
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"
OUTPUT_DIR = PROJECT_DIR / "output"


def fmt_money(v, places=0):
    if v is None:
        return "-"
    sign = "-" if v < 0 else ""
    return f"{sign}${abs(v):,.{places}f}"


def fmt_int(v):
    if v is None:
        return "-"
    return f"{int(v):,}"


def fmt_pct(v, places=1):
    if v is None:
        return "-"
    sign = "+" if v >= 0 else ""
    return f"{sign}{v:.{places}f}%"


def fmt_num(v, places=2):
    if v is None:
        return "-"
    return f"{v:.{places}f}"


def fmt_secs(v):
    if v is None:
        return "-"
    return f"{v:.0f}s"


def delta_class(v, good_direction="up"):
    """CSS class for a delta - green if good, red if bad."""
    if v is None or v == 0:
        return "neutral"
    is_up = v > 0
    if good_direction == "up":
        return "good" if is_up else "bad"
    return "bad" if is_up else "good"


def render_hero_table(brand, stores):
    t = brand["totals"]
    sl = brand["sl"]

    # POS GOV: pre is by definition $0 (didn't have Pathfinder); post is what they did
    rows = []
    rows.append(("Pathfinder POS GOV (post)", "$0 (no POS pre-install)", fmt_money(t["post_pos_gov"]), "-",
                 f"100% incremental - {fmt_money(t['post_pos_gov_per_week'])}/wk run-rate"))
    rows.append(("Pathfinder POS GOV (annualized)", "-", fmt_money(t["post_pos_gov_annualized"]), "-",
                 "Post weekly avg × 52"))
    rows.append(("Pathfinder POS orders (post)", "0", fmt_int(t["post_pos_orders"]), "-",
                 "In-store + Kiosk channels"))

    # Matched-window non-POS GOV (MP + Storefront combined)
    rows.append(("Non-POS GOV (matched window)",
                 fmt_money(t["matched_nonpos_pre_gov"]),
                 fmt_money(t["matched_nonpos_post_gov"]),
                 fmt_pct(t["matched_nonpos_gov_delta_pct"]),
                 "Marketplace + Storefront, equal-length pre/post"))
    rows.append(("Non-POS orders (matched window)",
                 fmt_int(t["matched_nonpos_pre_orders"]),
                 fmt_int(t["matched_nonpos_post_orders"]),
                 fmt_pct(t["matched_nonpos_orders_delta_pct"]),
                 "Marketplace + Storefront"))
    rows.append(("New customers (matched, MP+Storefront)",
                 fmt_int(t["matched_new_cx_pre"]),
                 fmt_int(t["matched_new_cx_post"]),
                 fmt_pct(t["matched_new_cx_delta_pct"]),
                 "New-to-store customers"))
    rows.append(("Repeat customers (matched, MP+Storefront)",
                 fmt_int(t["matched_repeat_cx_pre"]),
                 fmt_int(t["matched_repeat_cx_post"]),
                 fmt_pct(t["matched_repeat_cx_delta_pct"]),
                 "Returning customers"))

    # SL ROAS
    if sl["pre_ad_spend"] or sl["post_ad_spend"]:
        sl_delta = None
        if sl["pre_roas"] and sl["post_roas"]:
            sl_delta = (sl["post_roas"] - sl["pre_roas"]) / sl["pre_roas"] * 100.0
        rows.append(("Sponsored Listings ROAS",
                     f"{fmt_num(sl['pre_roas'])}x" if sl["pre_roas"] else "-",
                     f"{fmt_num(sl['post_roas'])}x" if sl["post_roas"] else "-",
                     fmt_pct(sl_delta),
                     f"Ad spend: {fmt_money(sl['pre_ad_spend'])} -> {fmt_money(sl['post_ad_spend'])}"))

    rows_html = ""
    for label, pre, post, delta, note in rows:
        cls = delta_class(None if delta == "-" else float(delta.rstrip("%").replace("+", "")) if delta and delta != "-" else None) if delta and delta != "-" else "neutral"
        rows_html += f"""
            <tr>
              <td><strong>{label}</strong></td>
              <td>{pre}</td>
              <td>{post}</td>
              <td class="{cls}">{delta}</td>
              <td class="note">{note}</td>
            </tr>"""

    return f"""
    <table class="hero">
      <thead>
        <tr><th>Hero metric</th><th>Pre</th><th>Post</th><th>Δ</th><th>Note</th></tr>
      </thead>
      <tbody>{rows_html}
      </tbody>
    </table>
    """


def render_normalized_runrate_table(brand):
    t = brand["totals"]
    rows = []
    rows.append(("Non-POS GOV ($/wk)",
                 fmt_money(t["full_pre_nonpos_gov_per_week"]),
                 fmt_money(t["post_nonpos_gov_per_week"]),
                 fmt_pct(t["nonpos_gov_weekly_delta_pct_vs_full_pre"])))
    rows.append(("Non-POS orders (/wk)",
                 fmt_int(t["full_pre_nonpos_orders_per_week"]),
                 fmt_int(t["post_nonpos_orders_per_week"]),
                 fmt_pct(t["nonpos_orders_weekly_delta_pct_vs_full_pre"])))
    rows.append(("POS GOV ($/wk)", "-", fmt_money(t["post_pos_gov_per_week"]), "100% net new"))
    rows.append(("Total DD-channel GOV ($/wk)",
                 fmt_money(t["full_pre_nonpos_gov_per_week"]),
                 fmt_money(t["post_nonpos_gov_per_week"] + t["post_pos_gov_per_week"]),
                 fmt_pct((((t["post_nonpos_gov_per_week"] + t["post_pos_gov_per_week"]) - t["full_pre_nonpos_gov_per_week"]) / t["full_pre_nonpos_gov_per_week"] * 100) if t["full_pre_nonpos_gov_per_week"] else None)))

    rows_html = ""
    for label, pre, post, delta in rows:
        cls = "neutral"
        if delta and delta != "-" and delta != "100% net new":
            try:
                cls = delta_class(float(delta.rstrip("%").replace("+", "")))
            except ValueError:
                cls = "neutral"
        elif delta == "100% net new":
            cls = "good"
        rows_html += f"""
            <tr>
              <td><strong>{label}</strong></td>
              <td>{pre}</td>
              <td>{post}</td>
              <td class="{cls}">{delta}</td>
            </tr>"""

    return f"""
    <table>
      <thead>
        <tr><th>Weekly run-rate</th><th>Pre-install baseline (6mo avg)</th><th>Post-install avg</th><th>Δ</th></tr>
      </thead>
      <tbody>{rows_html}
      </tbody>
    </table>
    """


def render_channel_breakdown(channels, label_pre, label_post, note=""):
    rows_html = ""
    # Order: In-store, Kiosk, Marketplace, Storefront
    order = ["In-store", "Kiosk", "Marketplace", "Storefront"]
    keys = order + [k for k in channels.keys() if k not in order]
    total_pre_orders = total_pre_gov = total_post_orders = total_post_gov = 0
    for ch in keys:
        if ch not in channels:
            continue
        v = channels[ch]
        pre_o = v["pre_orders"]
        pre_g = v["pre_subtotal"]
        post_o = v["post_orders"]
        post_g = v["post_subtotal"]
        total_pre_orders += pre_o
        total_pre_gov += pre_g
        total_post_orders += post_o
        total_post_gov += post_g
        orders_delta = (post_o - pre_o) / pre_o * 100.0 if pre_o else (None if not post_o else 999.0)
        gov_delta = (post_g - pre_g) / pre_g * 100.0 if pre_g else (None if not post_g else 999.0)

        def fmt_d(d):
            if d is None:
                return "-"
            if d == 999.0:
                return "net new"
            return fmt_pct(d)

        cls_o = "good" if orders_delta == 999.0 else delta_class(orders_delta if orders_delta != 999.0 else None)
        cls_g = "good" if gov_delta == 999.0 else delta_class(gov_delta if gov_delta != 999.0 else None)
        rows_html += f"""
            <tr>
              <td><strong>{ch}</strong></td>
              <td>{fmt_int(pre_o)}</td>
              <td>{fmt_int(post_o)}</td>
              <td class="{cls_o}">{fmt_d(orders_delta)}</td>
              <td>{fmt_money(pre_g)}</td>
              <td>{fmt_money(post_g)}</td>
              <td class="{cls_g}">{fmt_d(gov_delta)}</td>
            </tr>"""
    # Totals row
    rows_html += f"""
            <tr class="totals">
              <td><strong>Total</strong></td>
              <td>{fmt_int(total_pre_orders)}</td>
              <td>{fmt_int(total_post_orders)}</td>
              <td>{fmt_pct((total_post_orders - total_pre_orders) / total_pre_orders * 100 if total_pre_orders else None)}</td>
              <td>{fmt_money(total_pre_gov)}</td>
              <td>{fmt_money(total_post_gov)}</td>
              <td>{fmt_pct((total_post_gov - total_pre_gov) / total_pre_gov * 100 if total_pre_gov else None)}</td>
            </tr>"""

    return f"""
    <table>
      <thead>
        <tr>
          <th rowspan="2">Channel</th>
          <th colspan="3">Orders</th>
          <th colspan="3">GOV</th>
        </tr>
        <tr>
          <th>{label_pre}</th><th>{label_post}</th><th>Δ</th>
          <th>{label_pre}</th><th>{label_post}</th><th>Δ</th>
        </tr>
      </thead>
      <tbody>{rows_html}
      </tbody>
    </table>
    {f'<p class="note">{note}</p>' if note else ''}
    """


def render_mp_ops_table(mp_ops, mp_cancels):
    def delta(pre, post, good_direction="up"):
        if pre is None or pre == 0 or post is None:
            return "-", "neutral"
        d = (post - pre) / pre * 100.0
        cls = delta_class(d, good_direction)
        return fmt_pct(d), cls

    err_d, err_cls = delta(mp_ops.get("pre_error_rate_pct"), mp_ops.get("post_error_rate_pct"), "down")
    cnc_d, cnc_cls = delta(mp_cancels.get("pre_cancel_rate_pct"), mp_cancels.get("post_cancel_rate_pct"), "down")
    wait_d, wait_cls = delta(mp_ops.get("pre_avoidable_wait_seconds"), mp_ops.get("post_avoidable_wait_seconds"), "down")
    rate_d, rate_cls = delta(mp_ops.get("pre_avg_rating"), mp_ops.get("post_avg_rating"), "up")

    rows = [
        ("Completed MP orders", fmt_int(mp_ops.get("pre_completed_orders")), fmt_int(mp_ops.get("post_completed_orders")), "-", "neutral"),
        ("Missing/incorrect rate", fmt_pct(mp_ops.get("pre_error_rate_pct")), fmt_pct(mp_ops.get("post_error_rate_pct")), err_d, err_cls),
        ("Cancel rate (attempts)", fmt_pct(mp_cancels.get("pre_cancel_rate_pct")), fmt_pct(mp_cancels.get("post_cancel_rate_pct")), cnc_d, cnc_cls),
        ("Avoidable dasher wait", fmt_secs(mp_ops.get("pre_avoidable_wait_seconds")), fmt_secs(mp_ops.get("post_avoidable_wait_seconds")), wait_d, wait_cls),
        ("Avg merchant rating", fmt_num(mp_ops.get("pre_avg_rating"), 2), fmt_num(mp_ops.get("post_avg_rating"), 2), rate_d, rate_cls),
    ]
    rows_html = ""
    for label, pre, post, d, cls in rows:
        rows_html += f"""<tr><td><strong>{label}</strong></td><td>{pre}</td><td>{post}</td><td class="{cls}">{d}</td></tr>"""
    return f"""
    <table>
      <thead><tr><th>Marketplace ops</th><th>Matched pre</th><th>Matched post</th><th>Δ</th></tr></thead>
      <tbody>{rows_html}</tbody>
    </table>
    """


def render_sl_promos(sl, promos):
    def safe(v, formatter, *a):
        return formatter(v, *a) if v else "-"

    sl_rows = [
        ("Impressions", fmt_int(sl.get("pre_impressions")), fmt_int(sl.get("post_impressions"))),
        ("Clicks", fmt_int(sl.get("pre_clicks")), fmt_int(sl.get("post_clicks"))),
        ("Orders", fmt_int(sl.get("pre_orders")), fmt_int(sl.get("post_orders"))),
        ("Sales", fmt_money(sl.get("pre_sales")), fmt_money(sl.get("post_sales"))),
        ("Ad spend", fmt_money(sl.get("pre_ad_spend")), fmt_money(sl.get("post_ad_spend"))),
        ("ROAS", f"{fmt_num(sl.get('pre_roas'))}x" if sl.get("pre_roas") else "-",
                 f"{fmt_num(sl.get('post_roas'))}x" if sl.get("post_roas") else "-"),
        ("New cx via SL", fmt_int(sl.get("pre_new_cx")), fmt_int(sl.get("post_new_cx"))),
    ]
    sl_html = ""
    for l, pre, post in sl_rows:
        sl_html += f"<tr><td><strong>{l}</strong></td><td>{pre}</td><td>{post}</td></tr>"

    promo_rows = [
        ("Promo orders", fmt_int(promos.get("pre_orders")), fmt_int(promos.get("post_orders"))),
        ("Promo sales", fmt_money(promos.get("pre_sales")), fmt_money(promos.get("post_sales"))),
        ("DD-funded discount", fmt_money(promos.get("pre_dd_funded_discount")), fmt_money(promos.get("post_dd_funded_discount"))),
        ("Mx-funded discount", fmt_money(promos.get("pre_mx_funded_discount")), fmt_money(promos.get("post_mx_funded_discount"))),
        ("New cx via promos", fmt_int(promos.get("pre_new_cx")), fmt_int(promos.get("post_new_cx"))),
    ]
    promo_html = ""
    for l, pre, post in promo_rows:
        promo_html += f"<tr><td><strong>{l}</strong></td><td>{pre}</td><td>{post}</td></tr>"

    return f"""
    <div class="side-by-side">
      <div>
        <h3>Sponsored Listings</h3>
        <table><thead><tr><th></th><th>Matched pre</th><th>Matched post</th></tr></thead><tbody>{sl_html}</tbody></table>
      </div>
      <div>
        <h3>Promotions</h3>
        <table><thead><tr><th></th><th>Matched pre</th><th>Matched post</th></tr></thead><tbody>{promo_html}</tbody></table>
      </div>
    </div>
    """


def render_store(s):
    w = s["windows"]
    return f"""
    <div class="store-card">
      <h2>{s['store_name']} <span class="store-id">(Store {s['store_id']})</span></h2>
      <div class="store-meta">
        <strong>Install:</strong> {s['install_date']}
        &nbsp;|&nbsp; <strong>Tenure:</strong> {s['tenure_days']} days
        &nbsp;|&nbsp; <strong>Region:</strong> {s['metadata'].get('region_name')} / {s['metadata'].get('submarket_name')}
        &nbsp;|&nbsp; <strong>Cuisine:</strong> {s['metadata'].get('cuisine_type')}
        <br/>
        <strong>Matched window:</strong> {w['matched_pre_start']} → {w['matched_pre_end']} (pre) vs {w['post_start']} → {w['post_end']} (post)
      </div>

      <h3>Matched window: equal-length pre vs post ({w['post_days']}d each)</h3>
      {render_channel_breakdown(s['channels_matched'], "Pre " + str(w['matched_pre_days']) + "d", "Post " + str(w['post_days']) + "d")}

      <h3>Full pre baseline (6mo) vs post-to-date ({w['post_days']}d)</h3>
      {render_channel_breakdown(s['channels_full'], "Pre 180d", "Post " + str(w['post_days']) + "d", "Pre window is 180d, post is " + str(w['post_days']) + "d - compare via weekly run-rate, not totals.")}

      <h3>Marketplace operations (matched window)</h3>
      {render_mp_ops_table(s['mp_ops'], s['mp_cancels'])}

      <h3>Ads & Promos (matched window)</h3>
      {render_sl_promos(s['sl'], s['promos'])}
    </div>
    """


def render(data):
    brand = data["brand"]
    stores = data["stores"]
    today = data.get("today", date.today().isoformat())

    # Per-store install dates
    install_summary = "; ".join(f"{s['store_name'].split('(')[-1].rstrip(')')} installed {s['install_date']} ({s['tenure_days']}d)" for s in stores)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<title>Cracked Eggery - Pathfinder Growth Story</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; color: #333; max-width: 1100px; margin: 24px auto; padding: 0 20px; line-height: 1.5; }}
  h1 {{ color: #2C3E50; border-bottom: 3px solid #2C3E50; padding-bottom: 8px; margin-top: 0; }}
  h2 {{ color: #2C3E50; margin-top: 36px; border-bottom: 1px solid #ddd; padding-bottom: 4px; }}
  h3 {{ color: #34495E; margin-top: 24px; }}
  .subtitle {{ color: #555; font-size: 14px; margin-top: -6px; }}
  .caveat {{ background: #FFF8E1; border-left: 4px solid #F9A825; padding: 12px 16px; margin: 16px 0; font-size: 14px; }}
  .insight {{ background: #E8F5E9; border-left: 4px solid #2E7D32; padding: 12px 16px; margin: 16px 0; font-size: 14px; }}
  table {{ width: 100%; border-collapse: collapse; margin: 12px 0 18px 0; font-size: 14px; }}
  th, td {{ border: 1px solid #e0e0e0; padding: 8px 10px; text-align: right; }}
  th {{ background-color: #2C3E50; color: white; text-align: center; }}
  td:first-child {{ text-align: left; }}
  tr:nth-child(even) {{ background-color: #f9f9f9; }}
  tr.totals td {{ font-weight: 700; background-color: #ECEFF1; border-top: 2px solid #2C3E50; }}
  .hero {{ font-size: 15px; }}
  .hero td.note {{ font-size: 12px; color: #666; font-style: italic; text-align: left; }}
  .good {{ color: #2E7D32; font-weight: 600; }}
  .bad  {{ color: #D63B2F; font-weight: 600; }}
  .neutral {{ color: #777; }}
  .store-card {{ background: #fafafa; border: 1px solid #e0e0e0; padding: 16px 20px; margin: 24px 0; border-radius: 6px; }}
  .store-card h2 {{ margin-top: 0; }}
  .store-id {{ color: #888; font-size: 16px; font-weight: normal; }}
  .store-meta {{ font-size: 13px; color: #555; margin-bottom: 12px; }}
  .side-by-side {{ display: flex; gap: 18px; }}
  .side-by-side > div {{ flex: 1; }}
  .note {{ font-size: 12px; color: #666; font-style: italic; }}
  hr {{ border: none; border-top: 1px solid #ddd; margin: 32px 0; }}
  footer {{ color: #999; font-size: 11px; text-align: center; margin-top: 48px; }}
</style>
</head>
<body>

<h1>Cracked Eggery - Pathfinder Growth Story</h1>
<p class="subtitle">2 stores, ~2 months on Pathfinder. Generated {today}. Methodology: matched pre vs post windows (equal length per store) + 6-month pre baseline with weekly run-rate normalization.</p>

<div class="caveat">
  <strong>Caveats up front.</strong> n=2 stores; tenure is short (58d / 79d). Numbers in this report should be read as <em>directional signal</em>, not statistical proof. Where the post period and a 6mo pre period are compared, we normalize to weekly run-rate to keep the comparison apples-to-apples.
  <br/>
  <strong>Stores:</strong> {install_summary}
</div>

<h2>Executive Summary - Brand Total (Matched Window)</h2>
{render_hero_table(brand, stores)}

<h2>Brand Total - Weekly Run-Rate (vs 6mo Pre Baseline)</h2>
<p class="subtitle">Normalizes for the difference in window lengths. Pre baseline is the 6mo before each store installed, averaged to per-week.</p>
{render_normalized_runrate_table(brand)}

<h2>Brand Total - Channel Breakdown (Matched Window)</h2>
{render_channel_breakdown(brand['channels_matched'], "Matched pre", "Matched post", "Both Cracked Eggery stores summed. In-store + Kiosk = Pathfinder POS (100% incremental).")}

<h2>Brand Total - Marketplace Ops & Ads (Matched Window)</h2>
{render_mp_ops_table(brand['mp_ops'], brand['mp_cancels'])}

{render_sl_promos(brand['sl'], brand['promos'])}

<hr/>

<h2>Per-Store Breakdown</h2>
{''.join(render_store(s) for s in stores)}

<hr/>

<h2>Methodology</h2>
<ul>
  <li><strong>Matched window:</strong> equal-length pre vs post for each store (79d for Cleveland Park, 58d for 8th St). Cleanest apples-to-apples delta.</li>
  <li><strong>Full pre / weekly run-rate:</strong> 6mo before install vs post-to-date, normalized to per-week so window-length differences don't distort.</li>
  <li><strong>POS GOV is by definition 100% incremental</strong> - these stores had no in-store/kiosk channel reporting to DD before Pathfinder. Pre-install in-store/kiosk = $0 in <code>edw.merchant.fact_merchant_orders_portal</code>.</li>
  <li><strong>Marketplace ops</strong> (errors, rating, wait, cancellations) computed on the matched window only - these are completed-order-level metrics where seasonality matters less.</li>
  <li><strong>Sources:</strong> <code>edw.merchant.fact_merchant_orders_portal</code> (channels, ops, cx), <code>edw.ads.fact_sl_campaign_performance</code> (SL), <code>edw.ads.fact_promo_campaign_performance</code> (promos).</li>
</ul>

<footer>Generated by Claude Agent | {today} | Pathfinder Account Management</footer>

</body>
</html>
"""


def main():
    data = json.loads((DATA_DIR / "aggregate.json").read_text())
    html = render(data)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / "cracked-eggery-growth-story.html"
    out_path.write_text(html)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
