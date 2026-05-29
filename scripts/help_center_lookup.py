#!/usr/bin/env python3
"""Keyword lookup against data/help-center-map.json.

Usage:
  python3 scripts/help_center_lookup.py "card reader chip not reading"
  python3 scripts/help_center_lookup.py --top 3 "kiosk tipping setup"

Prints top-N matches as JSON: [{rank, score, title, url, section, category, excerpt}]
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP_PATH = ROOT / "data" / "help-center-map.json"

STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "to", "of", "in", "on", "at", "by", "for", "with", "from", "into",
    "and", "or", "but", "not", "no", "i", "you", "he", "she", "it", "we",
    "they", "my", "your", "our", "their", "this", "that", "these", "those",
    "do", "does", "did", "have", "has", "had", "will", "would", "should",
    "can", "could", "may", "might", "must", "shall", "what", "why", "how",
    "when", "where", "who", "which", "if", "then", "than", "so", "as",
    "about", "any", "some", "all", "each", "every", "just", "very",
}

WORD_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)?")


def tokenize(text: str) -> list[str]:
    return [t for t in WORD_RE.findall(text.lower()) if t not in STOPWORDS and len(t) > 1]


def score_article(query_tokens: list[str], article: dict, section_name: str, category_name: str) -> tuple[int, str, bool]:
    title = article["title"].lower()
    labels = " ".join(article.get("labels", [])).lower()
    body = article.get("body", "").lower()
    section = section_name.lower()

    score = 0
    matched_terms: set[str] = set()
    title_overlap = False  # True iff at least one query token appears in title/labels/section
    for tok in query_tokens:
        title_hits = title.count(tok)
        label_hits = labels.count(tok)
        section_hits = section.count(tok)
        body_hits = body.count(tok)
        if title_hits:
            score += 15 * title_hits
            matched_terms.add(tok)
            title_overlap = True
        if label_hits:
            score += 8 * label_hits
            matched_terms.add(tok)
            title_overlap = True
        if section_hits:
            score += 5 * section_hits
            matched_terms.add(tok)
            title_overlap = True
        if body_hits:
            score += min(body_hits, 5)
            matched_terms.add(tok)

    # Multi-term bonus: more unique query terms matched = higher confidence
    if len(matched_terms) >= 2:
        score += len(matched_terms) * 3

    # Build excerpt: first sentence containing any matched term
    excerpt = ""
    if matched_terms and body:
        sentences = re.split(r"(?<=[.!?])\s+", body[:3000])
        for s in sentences:
            sl = s.lower()
            if any(tok in sl for tok in matched_terms):
                excerpt = s.strip()[:280]
                break
        if not excerpt:
            excerpt = body[:280]
    elif body:
        excerpt = body[:280]

    return score, excerpt, title_overlap


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query", help="Search query string")
    parser.add_argument("--top", type=int, default=5, help="Number of results to return (default 5)")
    parser.add_argument("--min-score", type=int, default=20, help="Minimum score to return (default 20)")
    parser.add_argument(
        "--confident-only",
        action="store_true",
        help="Return only confident matches (score >= 30 AND title/label/section overlap)",
    )
    args = parser.parse_args()

    if not MAP_PATH.exists():
        sys.exit(f"Map not found at {MAP_PATH}. Run scripts/scrape_zendesk_help_center.py first.")

    data = json.loads(MAP_PATH.read_text())
    tokens = tokenize(args.query)
    if not tokens:
        print(json.dumps([]))
        return

    candidates = []
    for cat in data["categories"]:
        for sec in cat["sections"]:
            for art in sec["articles"]:
                score, excerpt, title_overlap = score_article(
                    tokens, art, sec["name"], cat["name"]
                )
                if score < args.min_score:
                    continue
                confident = score >= 30 and title_overlap
                if args.confident_only and not confident:
                    continue
                candidates.append(
                    {
                        "score": score,
                        "confident_match": confident,
                        "title_overlap": title_overlap,
                        "title": art["title"],
                        "url": art["url"],
                        "section": sec["name"],
                        "category": cat["name"],
                        "labels": art.get("labels", []),
                        "updated_at": art.get("updated_at"),
                        "article_id": art["id"],
                        "excerpt": excerpt,
                    }
                )

    candidates.sort(key=lambda x: (x["confident_match"], x["score"]), reverse=True)
    results = candidates[: args.top]
    for i, r in enumerate(results, start=1):
        r["rank"] = i

    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
