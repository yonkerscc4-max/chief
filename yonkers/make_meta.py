"""Write per-period collection notes for the reports.

Each period's report carries its own methodology notes, with the counts
computed from what was actually collected for that window rather than a
hand-written blurb that could drift from the data.
"""

import json
import os

from periods import PERIODS, in_period

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAW_DIR = os.path.join(ROOT, "raw")
OUT_DIR = os.path.join(ROOT, "output")

SHARED = [
    "Facebook comments were pulled from the most-commented posts inside the "
    "window. Heavily discussed posts are over-represented on purpose - that is "
    "where grievances collect - so these shares describe the complaint "
    "conversation, not the average post.",
    "Instagram contributes the comments returned alongside each post, a "
    "broader but shallower slice than Facebook.",
    "Emoji-only, tag-only and one-word reactions are counted in the total "
    "collected but excluded from the base used for the complaint rate, since "
    "they express no grievance either way.",
    "Comments posted by official city accounts are excluded, as the scrapers "
    "surface them alongside residents' replies.",
    "A category can rank low simply because the city rarely posted about it in "
    "this window. Treat the ranking as a measure of the conversation the "
    "city's own posts invited, not a census of civic opinion.",
]


def load(name):
    path = os.path.join(RAW_DIR, name)
    if not os.path.exists(path):
        return {"posts": {}, "comments": []}
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def main():
    fb, ig = load("facebook.json"), load("instagram.json")
    os.makedirs(OUT_DIR, exist_ok=True)

    for period in PERIODS:
        fb_posts = sum(1 for p in fb["posts"].values()
                       if in_period((p.get("d") or "")[:10], period))
        ig_posts = sum(1 for p in ig["posts"].values()
                       if in_period((p.get("d") or "")[:10], period))

        notes = [
            f"Coverage for this window: {fb_posts} Facebook posts and "
            f"{ig_posts} Instagram posts were sampled. Facebook's public feed "
            f"is paged in date-bounded slices, so this is a sample of the "
            f"period rather than every post the city published in it."
        ]
        if period["key"] in ("2021", "2022", "2023", "2024"):
            notes.append(
                "The city's pages drew far less engagement in this period than "
                "they do now - many posts carry no comments at all - so the "
                "complaint counts here are much smaller than in recent years. "
                "Compare shares between periods rather than raw counts.")
        notes.extend(SHARED)

        dest = os.path.join(OUT_DIR, f"meta_{period['key']}.json")
        with open(dest, "w", encoding="utf-8") as fh:
            json.dump({"limitations": notes}, fh, indent=1)
        print(f"{period['label']}: fb={fb_posts} ig={ig_posts} -> {os.path.basename(dest)}")


if __name__ == "__main__":
    main()
