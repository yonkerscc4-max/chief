"""Expand compact scrape dumps into the normalized record schema.

Scraped comments arrive through the MCP bridge, so they are transcribed to
disk in a deliberately terse form to keep the transfer small:

    raw/<name>.json
    {
      "platform": "facebook",
      "posts": {
        "<post_id>": {"u": "<post url>", "d": "<post ISO date>", "x": "<post text>"}
      },
      "comments": [
        {"p": "<post_id>", "t": "<comment text>", "d": "<ISO date>", "l": 3, "a": "author"}
      ]
    }

`ingest.py` expands those into full records in data/*.json, which is what
analyze.py consumes.
"""

import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAW_DIR = os.path.join(ROOT, "raw")
DATA_DIR = os.path.join(ROOT, "data")


def expand(bundle):
    platform = bundle.get("platform", "unknown")
    posts = bundle.get("posts", {})
    out = []
    for c in bundle.get("comments", []):
        post = posts.get(c.get("p", ""), {})
        text = (c.get("t") or "").strip()
        if not text:
            continue
        out.append({
            "platform": platform,
            "post_url": post.get("u", ""),
            "post_date": post.get("d", ""),
            "post_text": post.get("x", ""),
            "comment_text": text,
            "comment_date": c.get("d") or post.get("d", ""),
            "likes": int(c.get("l") or 0),
            "author": c.get("a", ""),
        })
    return out


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    total = 0
    for path in sorted(glob.glob(os.path.join(RAW_DIR, "*.json"))):
        with open(path, encoding="utf-8") as fh:
            bundle = json.load(fh)
        records = expand(bundle)
        name = os.path.splitext(os.path.basename(path))[0]
        dest = os.path.join(DATA_DIR, f"{name}.json")
        with open(dest, "w", encoding="utf-8") as fh:
            json.dump(records, fh, indent=1)
        print(f"{os.path.basename(path)} -> {len(records)} records")
        total += len(records)
    print(f"Total: {total} normalized comments")


if __name__ == "__main__":
    main()
