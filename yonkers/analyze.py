"""Ingest scraped comments, classify them, and emit report statistics.

Input : data/*.json  — lists of normalized comment records
Output: output/stats.json

A normalized comment record looks like:

    {
      "platform":     "facebook" | "instagram",
      "post_url":     str,
      "post_date":    ISO8601 str,
      "post_text":    str,
      "comment_text": str,
      "comment_date": ISO8601 str | None,
      "likes":        int,
      "author":       str
    }
"""

import json
import glob
import os
import re
from collections import Counter, defaultdict
from datetime import datetime

from taxonomy import classify, is_complaint

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA_DIR = os.path.join(ROOT, "data")
OUT_DIR = os.path.join(ROOT, "output")


def load_records():
    """Read every data/*.json file and return a flat, de-duplicated list."""
    records = []
    for path in sorted(glob.glob(os.path.join(DATA_DIR, "*.json"))):
        with open(path, "r", encoding="utf-8") as fh:
            try:
                chunk = json.load(fh)
            except json.JSONDecodeError as exc:
                print(f"  ! skipping {os.path.basename(path)}: {exc}")
                continue
        if isinstance(chunk, dict):
            chunk = chunk.get("items", [])
        records.extend(chunk)

    # De-duplicate on (author, text, post) — the same comment can arrive twice
    # when post-level and comment-level scrapes overlap.
    seen = set()
    unique = []
    for r in records:
        text = (r.get("comment_text") or "").strip()
        if not text:
            continue
        key = (r.get("author", ""), text[:200], r.get("post_url", ""))
        if key in seen:
            continue
        seen.add(key)
        unique.append(r)
    return unique


def year_of(record):
    """Best-effort year for a record, preferring the comment's own date."""
    for field in ("comment_date", "post_date"):
        val = record.get(field)
        if not val:
            continue
        try:
            return datetime.fromisoformat(str(val).replace("Z", "+00:00")).year
        except (ValueError, TypeError):
            m = re.search(r"(20\d{2})", str(val))
            if m:
                return int(m.group(1))
    return None


def analyze():
    records = load_records()
    print(f"Loaded {len(records)} unique comments")

    complaints = []
    for r in records:
        text = r.get("comment_text", "")
        if not is_complaint(text):
            continue
        primary, secondary, scores = classify(text)
        if not primary:
            continue
        r = dict(r)
        r["category"] = primary
        r["secondary"] = secondary
        r["score"] = scores.get(primary, 0)
        r["year"] = year_of(r)
        complaints.append(r)

    print(f"Identified {len(complaints)} classified complaints")

    counts = Counter(c["category"] for c in complaints)
    by_platform = defaultdict(Counter)
    by_year = defaultdict(Counter)
    likes_by_cat = defaultdict(int)

    for c in complaints:
        by_platform[c["category"]][c.get("platform", "unknown")] += 1
        if c.get("year"):
            by_year[c["category"]][c["year"]] += 1
        likes_by_cat[c["category"]] += int(c.get("likes") or 0)

    # Mentions counts every category a comment touches, not just the primary.
    mentions = Counter()
    for c in complaints:
        mentions[c["category"]] += 1
        for s in c["secondary"]:
            mentions[s] += 1

    total = len(complaints)
    ranked = []
    for cat, n in counts.most_common():
        ranked.append({
            "category": cat,
            "count": n,
            "share": round(100.0 * n / total, 1) if total else 0.0,
            "mentions": mentions[cat],
            "total_likes": likes_by_cat[cat],
            "avg_likes": round(likes_by_cat[cat] / n, 1) if n else 0.0,
            "by_platform": dict(by_platform[cat]),
            "by_year": dict(sorted(by_year[cat].items())),
            "examples": pick_examples(complaints, cat),
        })

    years_present = sorted({c["year"] for c in complaints if c.get("year")})
    stats = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_comments_scraped": len(records),
        "total_complaints": total,
        "complaint_rate": round(100.0 * total / len(records), 1) if records else 0.0,
        "years_covered": years_present,
        "platforms": dict(Counter(r.get("platform", "unknown") for r in records)),
        "comments_by_year": dict(sorted(Counter(
            y for y in (year_of(r) for r in records) if y
        ).items())),
        "categories": ranked,
    }

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "stats.json"), "w", encoding="utf-8") as fh:
        json.dump(stats, fh, indent=2)

    with open(os.path.join(OUT_DIR, "classified.json"), "w", encoding="utf-8") as fh:
        json.dump(complaints, fh, indent=2)

    print(f"\nTop categories ({total} complaints):")
    for row in ranked[:12]:
        print(f"  {row['count']:5d}  {row['share']:5.1f}%  {row['category']}")

    return stats


def pick_examples(complaints, category, n=8):
    """Pick illustrative verbatim comments for a category.

    Preference order: strong classifier score, then engagement, then length
    (long enough to read as a real grievance, short enough to quote).
    """
    pool = [c for c in complaints if c["category"] == category]

    def quotable(c):
        t = c["comment_text"].strip()
        return 40 <= len(t) <= 400

    good = [c for c in pool if quotable(c)] or pool
    good.sort(key=lambda c: (-c["score"], -int(c.get("likes") or 0)))

    picked, seen_authors, seen_text = [], set(), set()
    for c in good:
        a = c.get("author", "")
        if a and a in seen_authors:
            continue
        # Near-duplicate guard: the same grievance is often copy-pasted or
        # reposted verbatim across threads.
        fingerprint = re.sub(r"[^a-z0-9]+", " ", c["comment_text"].lower()).strip()[:120]
        if fingerprint in seen_text:
            continue
        seen_text.add(fingerprint)
        seen_authors.add(a)
        picked.append({
            "text": c["comment_text"].strip(),
            "author": a,
            "date": c.get("comment_date") or c.get("post_date"),
            "year": c.get("year"),
            "likes": int(c.get("likes") or 0),
            "platform": c.get("platform"),
            "post_url": c.get("post_url"),
            "post_text": (c.get("post_text") or "")[:220],
        })
        if len(picked) >= n:
            break
    return picked


if __name__ == "__main__":
    analyze()
