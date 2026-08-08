"""Extract Instagram comments from persisted Apify dataset pages.

Large MCP tool results are written to disk instead of being returned inline.
This reads every persisted `get-dataset-items` page, keeps the ones that look
like Instagram post records, and writes a compact bundle to raw/instagram.json
for ingest.py to expand.
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


def main():
    os.makedirs(RAW_DIR, exist_ok=True)
    posts, comments = {}, []
    seen_posts, seen_comments = set(), set()
    files = sorted(glob.glob(os.path.join(TOOL_RESULTS, "*get-dataset-items*.txt")))
    used = 0

    for path in files:
        try:
            with open(path, encoding="utf-8") as fh:
                payload = json.load(fh)
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        items = payload.get("items")
        if not isinstance(items, list) or not items:
            continue
        # Instagram post records carry an instagram.com url plus latestComments.
        if "instagram.com" not in str(items[0].get("url", "")):
            continue
        used += 1

        for post in items:
            purl = post.get("url") or ""
            if not purl:
                continue
            pid = purl.rstrip("/").split("/")[-1]
            if pid not in seen_posts:
                seen_posts.add(pid)
                posts[pid] = {
                    "u": purl,
                    "d": post.get("timestamp") or "",
                    "x": (post.get("caption") or "").replace("\n", " ")[:300],
                }
            for c in (post.get("latestComments") or []):
                text = (c.get("text") or "").strip()
                if not text:
                    continue
                cid = c.get("id") or f"{pid}:{text[:60]}"
                if cid in seen_comments:
                    continue
                seen_comments.add(cid)
                comments.append({
                    "p": pid,
                    "t": text,
                    "d": c.get("timestamp") or "",
                    "l": int(c.get("likesCount") or 0),
                    "a": c.get("ownerUsername") or "",
                })
                # Replies are nested one level deep and are real comments too.
                for r in (c.get("replies") or []):
                    rtext = (r.get("text") or "").strip()
                    if not rtext:
                        continue
                    rid = r.get("id") or f"{pid}:r:{rtext[:60]}"
                    if rid in seen_comments:
                        continue
                    seen_comments.add(rid)
                    comments.append({
                        "p": pid,
                        "t": rtext,
                        "d": r.get("timestamp") or "",
                        "l": int(r.get("likesCount") or 0),
                        "a": r.get("ownerUsername") or "",
                    })

    bundle = {"platform": "instagram", "posts": posts, "comments": comments}
    dest = os.path.join(RAW_DIR, "instagram.json")
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump(bundle, fh, ensure_ascii=False)

    print(f"pages used: {used}/{len(files)}")
    print(f"posts: {len(posts)}  comments: {len(comments)}")
    print(f"wrote {dest}")


if __name__ == "__main__":
    main()
