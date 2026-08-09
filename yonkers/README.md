# Yonkers Social Media Complaint Analysis

Scrapes public comments from the City of Yonkers' official Facebook and
Instagram accounts, classifies the grievances in them, and renders a PDF
report ranking the top complaint themes with verbatim examples.

## Pipeline

```
Apify scrape  →  data/*.json  →  analyze.py  →  output/stats.json  →  report.py  →  PDF
```

### 1. Collection

Comments are pulled with Apify actors:

| Source | Actor | Purpose |
| --- | --- | --- |
| Facebook | `apify/facebook-posts-scraper` | Enumerate page posts + comment counts |
| Facebook | `apify/facebook-comments-scraper` | Pull comments per post |
| Instagram | `apify/instagram-scraper` | Enumerate profile posts |
| Instagram | `apify/instagram-comment-scraper` | Pull comments per post |

Scraped results are normalized into `data/*.json` as records of the form:

```json
{
  "platform": "facebook",
  "post_url": "https://www.facebook.com/cityofyonkers/posts/...",
  "post_date": "2024-03-11T14:02:00.000Z",
  "post_text": "…",
  "comment_text": "…",
  "comment_date": "2024-03-11T15:40:00.000Z",
  "likes": 12,
  "author": "…"
}
```

### 2. Classification — `taxonomy.py`

Two stages, both keyword-driven so every number in the report traces back to
the phrases that produced it:

- **Complaint detection.** A comment counts only if it carries a grievance
  marker (a demand to fix something, a report of neglect, a "why hasn't…"
  question, an expression of frustration). Comments firing more praise markers
  than grievance markers are dropped, which keeps congratulatory replies out of
  the denominator.
- **Category scoring.** Weighted patterns (3 = unambiguous, 2 = strong,
  1 = weak) score each of 13 civic categories. The top scorer becomes the
  comment's primary category; other categories scoring ≥3 are kept as
  secondary "mentions".

### 3. Analysis — `analyze.py`

De-duplicates comments, classifies them, and writes `output/stats.json` with
per-category counts, shares, platform splits, year-by-year series, engagement,
and curated verbatim examples.

```bash
cd yonkers && python3 analyze.py
```

### 4. Report — `report.py`

Renders the PDF: cover, methodology, top-10 ranking with bar chart, multi-year
trend lines, per-category pages with quotes and sparklines, and a full
category appendix.

```bash
cd yonkers && python3 report.py
```

## Requirements

```bash
pip install reportlab matplotlib
```

## Notes on interpretation

The counts describe complaints residents chose to post publicly on the city's
own channels. That is a strong signal of what frustrates the engaged public,
but it is not a representative survey of Yonkers residents — volume is shaped
by what the city posts about, by which posts go viral, and by moderation.
