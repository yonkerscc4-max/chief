"""Extract Facebook post metadata and comments from persisted Apify pages.

Handles two shapes of persisted `get-dataset-items` output:

* post records  — from facebook-posts-scraper (carry `time` + optional
  `topComments`, which are real comments included with the post and cost
  nothing extra)
* comment records — from facebook-comments-scraper (carry `text` plus a
  `facebookUrl`/`postUrl` pointing back at the post)

Writes raw/facebook.json for ingest.py, and posts.json listing every post
with its comment count so scrape targets can be chosen by engagement.
"""

import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAW_DIR = os.path.join(ROOT, "raw")

TOOL_RESULTS = sys.argv[1] if len(sys.argv) > 1 else (
    "/root/.claude/projects/-home-user-chief/"
    "06a669e7-2ca9-5ddb-a516-fb6254cc5389/tool-results"
)


def post_id(url):
    return (url or "").rstrip("/").split("/")[-1][:60]


def load_pages():
    for path in sorted(glob.glob(os.path.join(TOOL_RESULTS, "*get-dataset-items*.txt"))):
        try:
            with open(path, encoding="utf-8") as fh:
                payload = json.load(fh)
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        items = payload.get("items")
        if isinstance(items, list) and items:
            yield items


def main():
    os.makedirs(RAW_DIR, exist_ok=True)
    posts, comments = {}, []
    counts = {}
    seen_c = set()

    for items in load_pages():
        head = items[0]
        blob = json.dumps(head)
        if "facebook.com" not in blob:
            continue

        # --- post records -------------------------------------------------
        if "time" in head and "instagram.com" not in blob:
            for p in items:
                url = p.get("url") or ""
                if not url:
                    continue
                pid = post_id(url)
                posts.setdefault(pid, {
                    "u": url,
                    "d": p.get("time") or "",
                    "x": (p.get("text") or "").replace("\n", " ")[:300],
                })
                counts[pid] = max(counts.get(pid, 0), int(p.get("comments") or 0))
                for c in (p.get("topComments") or []):
                    text = (c.get("text") or "").strip()
                    if not text:
                        continue
                    cid = c.get("commentId") or c.get("id") or f"{pid}:{text[:60]}"
                    if cid in seen_c:
                        continue
                    seen_c.add(cid)
                    comments.append({
                        "p": pid, "t": text, "d": c.get("date") or "",
                        "l": int(c.get("likesCount") or 0),
                        "a": c.get("profileName") or "",
                    })

        # --- comment records ----------------------------------------------
        elif "text" in head and ("postUrl" in head or "facebookUrl" in head):
            for c in items:
                text = (c.get("text") or "").strip()
                if not text:
                    continue
                purl = c.get("postUrl") or c.get("facebookUrl") or ""
                pid = post_id(purl)
                cid = c.get("id") or c.get("commentId") or f"{pid}:{text[:60]}"
                if cid in seen_c:
                    continue
                seen_c.add(cid)
                comments.append({
                    "p": pid, "t": text, "d": c.get("date") or "",
                    "l": int(c.get("likesCount") or 0),
                    "a": (c.get("profileName") or ""),
                })
                posts.setdefault(pid, {
                    "u": purl,
                    "d": c.get("date") or "",
                    "x": (c.get("postTitle") or "").replace("\n", " ")[:300],
                })

    bundle = {"platform": "facebook", "posts": posts, "comments": comments}
    with open(os.path.join(RAW_DIR, "facebook.json"), "w", encoding="utf-8") as fh:
        json.dump(bundle, fh, ensure_ascii=False)

    ranked = sorted(counts.items(), key=lambda kv: -kv[1])
    with open(os.path.join(RAW_DIR, "posts.json"), "w", encoding="utf-8") as fh:
        json.dump([{"id": p, "url": posts[p]["u"], "date": posts[p]["d"], "n": n}
                   for p, n in ranked if p in posts], fh, indent=1)

    print(f"posts: {len(posts)}  comments so far: {len(comments)}")
    print(f"posts with >0 comments: {sum(1 for _, n in ranked if n)}")
    print(f"comments available on page: {sum(counts.values())}")


if __name__ == "__main__":
    main()
