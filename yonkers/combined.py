"""Render the six period reports as one document, led by a comparison.

Produces output/Yonkers_Complaints_2021-2026_Combined.pdf: a cover, a
cross-period comparison (how each theme's share moved from 2021 to 2026),
then every period's full report as its own section.
"""

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer,
    Table, TableStyle,
)

import report as R
from periods import PERIODS

OUT_DIR = R.OUT_DIR
SHORT = {"2021": "2021", "2022": "2022", "2023": "2023",
         "2024": "2024", "2025": "2025", "2026": "2026*"}


def load_all():
    out = []
    for p in PERIODS:
        path = os.path.join(OUT_DIR, f"stats_{p['key']}.json")
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as fh:
            out.append((p, json.load(fh)))
    return out


def share_matrix(loaded, top_n=12):
    """Categories ranked by mean share, with each period's share."""
    cats = {}
    for _, st in loaded:
        for row in st["categories"]:
            cats.setdefault(row["category"], {})
    for period, st in loaded:
        by = {r["category"]: r["share"] for r in st["categories"]}
        for c in cats:
            cats[c][period["key"]] = by.get(c, 0.0)
    ranked = sorted(cats.items(),
                    key=lambda kv: -sum(kv[1].values()) / max(len(kv[1]), 1))
    return ranked[:top_n]


def chart_heatmap(loaded, matrix, path):
    keys = [p["key"] for p, _ in loaded]
    labels = [c for c, _ in matrix]
    data = np.array([[vals.get(k, 0.0) for k in keys] for _, vals in matrix])

    fig, ax = plt.subplots(figsize=(7.4, 0.42 * len(labels) + 1.3), dpi=200)
    im = ax.imshow(data, cmap="RdPu", aspect="auto", vmin=0)

    ax.set_xticks(range(len(keys)))
    ax.set_xticklabels([SHORT[k] for k in keys], fontsize=9, color="#12263F")
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=8.5, color="#12263F")
    ax.tick_params(length=0)

    peak = data.max() if data.size else 1
    for i in range(len(labels)):
        for j in range(len(keys)):
            v = data[i, j]
            if v <= 0:
                continue
            ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=7.6,
                    color="white" if v > peak * 0.55 else "#12263F")

    for side in ("top", "right", "bottom", "left"):
        ax.spines[side].set_visible(False)
    cb = fig.colorbar(im, ax=ax, shrink=0.65, pad=0.02)
    cb.set_label("% of that period's complaints", fontsize=8, color="#3E5C76")
    cb.ax.tick_params(labelsize=7.5, length=0)
    cb.outline.set_visible(False)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def chart_volume_by_period(loaded, path):
    keys = [SHORT[p["key"]] for p, _ in loaded]
    subs = [st["substantive_comments"] for _, st in loaded]
    comps = [st["total_complaints"] for _, st in loaded]
    x = np.arange(len(keys))

    fig, ax = plt.subplots(figsize=(7.4, 2.6), dpi=200)
    ax.bar(x - 0.2, subs, width=0.4, color="#3E5C76", label="Substantive comments")
    ax.bar(x + 0.2, comps, width=0.4, color="#C1443C", label="Complaints")
    ax.set_xticks(x)
    ax.set_xticklabels(keys, fontsize=9, color="#12263F")
    ax.tick_params(labelsize=8, colors="#8899AA", length=0)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("bottom", "left"):
        ax.spines[side].set_color("#D6DCE4")
    ax.grid(axis="y", color="#EDF0F4", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.legend(fontsize=8, frameon=False)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def build_combined():
    loaded = load_all()
    s = R.build_styles()
    chart_dir = os.path.join(OUT_DIR, "charts", "combined")
    os.makedirs(chart_dir, exist_ok=True)
    story = []

    total_c = sum(st["total_comments_scraped"] for _, st in loaded)
    total_s = sum(st["substantive_comments"] for _, st in loaded)
    total_x = sum(st["total_complaints"] for _, st in loaded)

    # ---------------- Cover ----------------
    story.append(Spacer(1, 1.45 * inch))
    story.append(Paragraph("What Yonkers Residents<br/>Complain About",
                           s["title"]))
    story.append(Spacer(1, 0.16 * inch))
    story.append(Paragraph(
        "Six reporting periods, 2021 – 2026<br/>"
        "Public comments on the City of Yonkers' official Facebook and "
        "Instagram accounts", s["subtitle"]))
    story.append(Spacer(1, 0.45 * inch))

    rows = [["Periods covered", "6 windows, March – November 2021 through 2025, "
                                "plus March – July 2026"],
            ["Comments collected", f"{total_c:,}"],
            ["Of which substantive", f"{total_s:,}"],
            ["Complaints identified", f"{total_x:,}"],
            ["Sources", "facebook.com/cityofyonkers · instagram.com/cityofyonkers"]]
    t = Table(rows, colWidths=[1.75 * inch, 4.15 * inch])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), R.SLATE),
        ("TEXTCOLOR", (1, 0), (1, -1), R.NAVY),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LINEBELOW", (0, 0), (-1, -2), 0.4, R.RULE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(t)
    story.append(PageBreak())

    # ---------------- Comparison ----------------
    story.append(Paragraph("How the complaints changed, 2021 – 2026", s["h1"]))
    story.append(Paragraph(
        "Each period was analysed separately and is reproduced in full later "
        "in this document. This section sets them side by side. The figure in "
        "each cell is that theme's share of all complaints in that period, so "
        "columns are comparable even though the periods differ enormously in "
        "volume — 2021 yields 28 complaints, 2026 yields 191.", s["body"]))

    matrix = share_matrix(loaded)
    heat = os.path.join(chart_dir, "heatmap.png")
    chart_heatmap(loaded, matrix, heat)
    story.append(Spacer(1, 0.05 * inch))
    story.append(Image(heat, width=6.5 * inch,
                       height=min(6.6, 0.42 * len(matrix) + 1.3) / 7.4 * 6.5 * inch))
    story.append(Paragraph(
        "* 2026 covers March – July only; every other column is March – November.",
        s["small"]))
    story.append(PageBreak())

    # ---------------- Leaders + volume ----------------
    story.append(Paragraph("What led each period", s["h1"]))
    lead_rows = [["Period", "Largest complaint theme", "Share", "Complaints"]]
    for period, st in loaded:
        top = st["categories"][0] if st["categories"] else None
        lead_rows.append([
            period["label"],
            top["category"] if top else "—",
            f"{top['share']}%" if top else "—",
            f"{st['total_complaints']:,}",
        ])
    t = Table(lead_rows, colWidths=[1.85 * inch, 2.75 * inch,
                                    0.75 * inch, 1.0 * inch], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), R.NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (1, 1), (1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.8),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, R.LIGHT]),
        ("TEXTCOLOR", (1, 1), (1, -1), R.NAVY),
        ("GRID", (0, 0), (-1, -1), 0.3, R.RULE),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(KeepTogether(t))
    story.append(Spacer(1, 0.22 * inch))

    story.append(Paragraph("Sample size behind each period", s["h2"]))
    story.append(Paragraph(
        "The city's pages drew far less engagement early in the decade, so the "
        "early periods rest on a much smaller base. Read 2021 and 2022 as "
        "indicative of what was being raised, not as precise measurements, and "
        "compare shares between periods rather than raw counts.", s["body"]))
    vol = os.path.join(chart_dir, "volume_by_period.png")
    chart_volume_by_period(loaded, vol)
    story.append(Image(vol, width=6.5 * inch, height=2.28 * inch))
    story.append(Spacer(1, 0.18 * inch))

    story.append(Paragraph("Reading the comparison", s["h2"]))
    story.append(Paragraph(
        "Two caveats govern every number here. First, coverage is not even: "
        "Instagram's public feed could not be paged back past March 2023, so "
        "2021 and 2022 are Facebook-only, while later periods draw on both "
        "platforms. Second, a theme can fade from the table because the city "
        "stopped posting about it, not because residents stopped caring — "
        "these are the complaints the city's own posts invited. Where a theme "
        "moves sharply, check whether the sample behind it moved too.",
        s["body"]))
    story.append(PageBreak())

    # ---------------- Period sections ----------------
    for period, st in loaded:
        meta_path = os.path.join(OUT_DIR, f"meta_{period['key']}.json")
        meta = {}
        if os.path.exists(meta_path):
            with open(meta_path, encoding="utf-8") as fh:
                meta = json.load(fh)

        R.CHART_DIR = os.path.join(OUT_DIR, "charts", period["key"])
        os.makedirs(R.CHART_DIR, exist_ok=True)

        story.append(Spacer(1, 2.6 * inch))
        story.append(Paragraph(period["label"], s["title"]))
        story.append(Spacer(1, 0.12 * inch))
        story.append(Paragraph(
            f"{st['total_comments_scraped']:,} comments collected · "
            f"{st['substantive_comments']:,} substantive · "
            f"{st['total_complaints']:,} complaints "
            f"({st['complaint_rate']}%)", s["subtitle"]))
        story.append(PageBreak())
        story.extend(R.build(st, meta, include_cover=False))
        story.append(PageBreak())

    return story


def main():
    out_path = os.path.join(
        OUT_DIR, "Yonkers_Complaints_2021-2026_Combined.pdf")
    doc = SimpleDocTemplate(
        out_path, pagesize=LETTER,
        leftMargin=0.75 * inch, rightMargin=0.75 * inch,
        topMargin=0.85 * inch, bottomMargin=0.75 * inch,
        title="What Yonkers Residents Complain About — 2021-2026",
        author="Social Media Listening Analysis",
        subject="Complaint themes across six reporting periods, 2021-2026")

    decorate = R.make_page_decorator(
        "What Yonkers Residents Complain About · 2021 – 2026")
    doc.build(build_combined(), onFirstPage=decorate, onLaterPages=decorate)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
