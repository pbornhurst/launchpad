#!/usr/bin/env python3
"""Scrape doordash-instore Zendesk help center via Help Center API.

Pulls every category → section → article. Saves two files:
  data/help-center-map.json — programmatic map (full article bodies stripped of HTML)
  data/help-center-map.md   — human-skimmable index

Auth: reads ZENDESK_EMAIL + ZENDESK_API_TOKEN + ZENDESK_SUBDOMAIN from .env.
Run: python3 scripts/scrape_zendesk_help_center.py
"""

import base64
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DATA.mkdir(parents=True, exist_ok=True)

# Load .env manually (no python-dotenv dep)
env_path = ROOT / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

EMAIL = os.environ.get("ZENDESK_EMAIL")
TOKEN = os.environ.get("ZENDESK_API_TOKEN")
SUBDOMAIN = os.environ.get("ZENDESK_SUBDOMAIN", "doordash-instore")
LOCALE = "en-us"

if not EMAIL or not TOKEN:
    sys.exit("Missing ZENDESK_EMAIL or ZENDESK_API_TOKEN in .env")

BASE = f"https://{SUBDOMAIN}.zendesk.com/api/v2/help_center/{LOCALE}"
AUTH_HEADER = "Basic " + base64.b64encode(f"{EMAIL}/token:{TOKEN}".encode()).decode()


def get(path: str, per_page: int = 100):
    """GET with pagination. Yields each result item."""
    url = f"{BASE}/{path}?per_page={per_page}"
    while url:
        req = urllib.request.Request(
            url,
            headers={"Authorization": AUTH_HEADER, "Accept": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = json.loads(resp.read().decode())
        except Exception as e:
            print(f"  ERROR fetching {url}: {e}", file=sys.stderr)
            return
        # Detect which key holds the records.
        key = next(
            (k for k in ("categories", "sections", "articles") if k in payload),
            None,
        )
        if not key:
            return
        for item in payload[key]:
            yield item
        url = payload.get("next_page")
        if url:
            time.sleep(0.1)  # be polite


TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


def strip_html(s: str) -> str:
    if not s:
        return ""
    s = TAG_RE.sub(" ", s)
    s = html.unescape(s)
    s = WS_RE.sub(" ", s).strip()
    return s


def main():
    print("Fetching categories…")
    categories = list(get("categories.json"))
    print(f"  → {len(categories)} categories")

    print("Fetching sections per category…")
    sections_by_cat = {}
    for cat in categories:
        secs = list(get(f"categories/{cat['id']}/sections.json"))
        sections_by_cat[cat["id"]] = secs
        print(f"  {cat['name']!r}: {len(secs)} sections")

    print("Fetching articles per section…")
    articles_by_sec = {}
    total_articles = 0
    for cat in categories:
        for sec in sections_by_cat[cat["id"]]:
            arts = list(get(f"sections/{sec['id']}/articles.json"))
            articles_by_sec[sec["id"]] = arts
            total_articles += len(arts)
    print(f"  → {total_articles} articles total")

    # Build programmatic map
    map_obj = {
        "subdomain": SUBDOMAIN,
        "locale": LOCALE,
        "scraped_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "category_count": len(categories),
        "article_count": total_articles,
        "categories": [],
    }
    for cat in categories:
        cat_entry = {
            "id": cat["id"],
            "name": cat["name"],
            "url": cat["html_url"],
            "description": strip_html(cat.get("description", "")),
            "sections": [],
        }
        for sec in sections_by_cat[cat["id"]]:
            sec_entry = {
                "id": sec["id"],
                "name": sec["name"],
                "url": sec["html_url"],
                "description": strip_html(sec.get("description", "")),
                "articles": [],
            }
            for art in articles_by_sec[sec["id"]]:
                body_text = strip_html(art.get("body") or "")
                sec_entry["articles"].append(
                    {
                        "id": art["id"],
                        "title": art["title"],
                        "url": art["html_url"],
                        "updated_at": art.get("updated_at"),
                        "labels": art.get("label_names") or [],
                        "snippet": body_text[:300],
                        "body": body_text,
                    }
                )
            cat_entry["sections"].append(sec_entry)
        map_obj["categories"].append(cat_entry)

    # Write JSON
    json_path = DATA / "help-center-map.json"
    json_path.write_text(json.dumps(map_obj, indent=2, ensure_ascii=False))
    print(f"Wrote {json_path}")

    # Write markdown index (titles + URLs only, no bodies)
    md_lines = [
        "# DoorDash In-Store Help Center — Map",
        "",
        f"_Scraped {map_obj['scraped_at']} from `{SUBDOMAIN}.zendesk.com`. "
        f"{len(categories)} categories, {total_articles} articles._",
        "",
        "Use `data/help-center-map.json` for keyword search (each article has a `body` field). ",
        "This file is the human-readable index.",
        "",
    ]
    for cat in map_obj["categories"]:
        md_lines.append(f"## {cat['name']}")
        md_lines.append(f"<{cat['url']}>")
        if cat["description"]:
            md_lines.append(f"\n_{cat['description']}_")
        md_lines.append("")
        for sec in cat["sections"]:
            md_lines.append(f"### {sec['name']}")
            md_lines.append(f"<{sec['url']}>")
            if sec["description"]:
                md_lines.append(f"_{sec['description']}_")
            md_lines.append("")
            for art in sec["articles"]:
                md_lines.append(f"- [{art['title']}]({art['url']})")
            md_lines.append("")
        md_lines.append("---")
        md_lines.append("")

    md_path = DATA / "help-center-map.md"
    md_path.write_text("\n".join(md_lines))
    print(f"Wrote {md_path}")

    print(f"\nDone. {len(categories)} categories, {total_articles} articles.")


if __name__ == "__main__":
    main()
