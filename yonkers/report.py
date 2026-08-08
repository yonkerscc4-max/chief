"""Render the Yonkers social-media complaint analysis as a PDF report.

Reads output/stats.json (written by analyze.py) and produces
output/Yonkers_Social_Media_Complaint_Report.pdf
"""

import argparse
import json
import os
import textwrap
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from periods import PERIODS
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image, KeepTogether, PageBreak, PageTemplate,
    Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT_DIR = os.path.join(ROOT, "output")
CHART_DIR = os.path.join(OUT_DIR, "charts")

# --------------------------------------------------------------------------
# Palette
# --------------------------------------------------------------------------
NAVY = colors.HexColor("#12263F")
SLATE = colors.HexColor("#3E5C76")
ACCENT = colors.HexColor("#C1443C")
LIGHT = colors.HexColor("#F2F4F7")
MID = colors.HexColor("#8899AA")
RULE = colors.HexColor("#D6DCE4")

BAR_COLORS = [
    "#12263F", "#1F3A5F", "#2E5077", "#3E5C76", "#527A94",
    "#6E93A8", "#8FAFBE", "#A9C3CE", "#C2D4DC", "#D8E3E8",
]


def esc(text):
    """Escape text for reportlab's mini-HTML paragraph markup."""
    return (str(text).replace("&", "&amp;")
                     .replace("<", "&lt;")
                     .replace(">", "&gt;"))


# --------------------------------------------------------------------------
# Styles
# --------------------------------------------------------------------------
def build_styles():
    ss = getSampleStyleSheet()
    s = {}
    s["title"] = ParagraphStyle(
        "title", parent=ss["Title"], fontName="Helvetica-Bold",
        fontSize=30, leading=35, textColor=NAVY, alignment=TA_CENTER,
        spaceAfter=6)
    s["subtitle"] = ParagraphStyle(
        "subtitle", parent=ss["Normal"], fontName="Helvetica",
        fontSize=14, leading=19, textColor=SLATE, alignment=TA_CENTER)
    s["cover_meta"] = ParagraphStyle(
        "cover_meta", parent=ss["Normal"], fontName="Helvetica",
        fontSize=10, leading=15, textColor=MID, alignment=TA_CENTER)
    s["h1"] = ParagraphStyle(
        "h1", parent=ss["Heading1"], fontName="Helvetica-Bold",
        fontSize=17, leading=21, textColor=NAVY, spaceBefore=4, spaceAfter=10)
    s["h2"] = ParagraphStyle(
        "h2", parent=ss["Heading2"], fontName="Helvetica-Bold",
        fontSize=12.5, leading=16, textColor=SLATE, spaceBefore=12, spaceAfter=5)
    s["body"] = ParagraphStyle(
        "body", parent=ss["Normal"], fontName="Helvetica",
        fontSize=10, leading=15, textColor=colors.HexColor("#1D2733"),
        alignment=TA_JUSTIFY, spaceAfter=7)
    s["small"] = ParagraphStyle(
        "small", parent=ss["Normal"], fontName="Helvetica",
        fontSize=8.5, leading=12, textColor=MID)
    s["quote"] = ParagraphStyle(
        "quote", parent=ss["Normal"], fontName="Helvetica-Oblique",
        fontSize=9.5, leading=13.5, textColor=colors.HexColor("#22303F"),
        leftIndent=10, rightIndent=6, spaceAfter=2)
    s["quote_meta"] = ParagraphStyle(
        "quote_meta", parent=ss["Normal"], fontName="Helvetica",
        fontSize=7.8, leading=10, textColor=MID, leftIndent=10, spaceAfter=8)
    s["rank_num"] = ParagraphStyle(
        "rank_num", parent=ss["Normal"], fontName="Helvetica-Bold",
        fontSize=25, leading=27, textColor=ACCENT)
    s["cat_title"] = ParagraphStyle(
        "cat_title", parent=ss["Normal"], fontName="Helvetica-Bold",
        fontSize=15, leading=18, textColor=NAVY)
    s["cat_stat"] = ParagraphStyle(
        "cat_stat", parent=ss["Normal"], fontName="Helvetica",
        fontSize=9, leading=12.5, textColor=SLATE)
    return s


# --------------------------------------------------------------------------
# Charts
# --------------------------------------------------------------------------
def chart_top_categories(stats, path, top_n=10):
    rows = stats["categories"][:top_n]
    labels = [r["category"] for r in rows][::-1]
    values = [r["count"] for r in rows][::-1]
    shares = [r["share"] for r in rows][::-1]

    fig, ax = plt.subplots(figsize=(7.4, 4.6), dpi=200)
    wrapped = ["\n".join(textwrap.wrap(l, 26)) for l in labels]
    bars = ax.barh(wrapped, values, color=BAR_COLORS[::-1][-len(values):],
                   edgecolor="none", height=0.68)

    span = max(values) if values else 1
    for bar, val, share in zip(bars, values, shares):
        ax.text(bar.get_width() + span * 0.014,
                bar.get_y() + bar.get_height() / 2,
                f"{val:,}  ({share}%)", va="center", ha="left",
                fontsize=8.5, color="#3E5C76")

    ax.set_xlabel("Complaint comments", fontsize=9, color="#3E5C76")
    ax.set_xlim(0, span * 1.22)
    ax.tick_params(axis="y", labelsize=8.5, colors="#12263F", length=0)
    ax.tick_params(axis="x", labelsize=8, colors="#8899AA")
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color("#D6DCE4")
    ax.grid(axis="x", color="#EDF0F4", linewidth=0.8)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def month_axis(stats):
    """Ordered YYYY-MM buckets present in the sample."""
    return sorted(stats.get("comments_by_month", {}).keys())


def month_labels(months):
    """Label every other month as 'Mon YY' to keep the axis readable."""
    names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
             "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    out = []
    for i, m in enumerate(months):
        y, mm = m.split("-")
        out.append(f"{names[int(mm) - 1]} {y[2:]}" if i % 2 == 0 else "")
    return out


def chart_trend(stats, path, top_n=5):
    rows = stats["categories"][:top_n]
    months = month_axis(stats)
    if len(months) < 2:
        return False
    x = range(len(months))

    fig, ax = plt.subplots(figsize=(7.4, 3.5), dpi=200)
    for i, r in enumerate(rows):
        bm = r.get("by_month", {})
        series = [bm.get(m, 0) for m in months]
        ax.plot(list(x), series, marker="o", markersize=3.2, linewidth=1.9,
                color=BAR_COLORS[i], label=r["category"])

    ax.set_ylabel("Complaints", fontsize=9, color="#3E5C76")
    ax.set_xticks(list(x))
    ax.set_xticklabels(month_labels(months), fontsize=7.5, rotation=0)
    ax.tick_params(labelsize=8, colors="#8899AA")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("bottom", "left"):
        ax.spines[side].set_color("#D6DCE4")
    ax.grid(color="#EDF0F4", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.legend(fontsize=7.4, frameon=False, ncol=2, loc="upper left")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return True


def chart_volume(stats, path):
    data = stats.get("comments_by_month", {})
    months = month_axis(stats)
    if not months:
        return False
    x = range(len(months))
    fig, ax = plt.subplots(figsize=(7.4, 2.4), dpi=200)
    ax.bar(list(x), [data[m] for m in months], color="#3E5C76",
           edgecolor="none", width=0.68)
    ax.set_ylabel("Comments sampled", fontsize=8.5, color="#3E5C76")
    ax.set_xticks(list(x))
    ax.set_xticklabels(month_labels(months), fontsize=7.5)
    ax.tick_params(labelsize=8, colors="#8899AA")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("bottom", "left"):
        ax.spines[side].set_color("#D6DCE4")
    ax.grid(axis="y", color="#EDF0F4", linewidth=0.8)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return True


def chart_category_spark(row, path, months):
    if len(months) < 2:
        return False
    bm = row.get("by_month", {})
    series = [bm.get(m, 0) for m in months]
    x = list(range(len(months)))
    fig, ax = plt.subplots(figsize=(3.0, 0.72), dpi=200)
    ax.plot(x, series, color="#C1443C", linewidth=1.7)
    ax.fill_between(x, series, color="#C1443C", alpha=0.13)
    ax.set_xticks([])
    ax.set_yticks([])
    for side in ("top", "right", "bottom", "left"):
        ax.spines[side].set_visible(False)
    fig.tight_layout(pad=0.1)
    fig.savefig(path, bbox_inches="tight", facecolor="white", transparent=False)
    plt.close(fig)
    return True


# --------------------------------------------------------------------------
# Page furniture
# --------------------------------------------------------------------------
def make_page_decorator(title):
    def decorate(canvas, doc):
        canvas.saveState()
        if doc.page > 1:
            canvas.setStrokeColor(RULE)
            canvas.setLineWidth(0.6)
            canvas.line(0.75 * inch, LETTER[1] - 0.62 * inch,
                        LETTER[0] - 0.75 * inch, LETTER[1] - 0.62 * inch)
            canvas.setFont("Helvetica", 7.6)
            canvas.setFillColor(MID)
            canvas.drawString(0.75 * inch, LETTER[1] - 0.55 * inch, title)
            canvas.drawRightString(LETTER[0] - 0.75 * inch,
                                   LETTER[1] - 0.55 * inch,
                                   "City of Yonkers · Social Media Listening")
            canvas.setFont("Helvetica", 8)
            canvas.drawCentredString(LETTER[0] / 2, 0.45 * inch, str(doc.page))
        canvas.restoreState()
    return decorate


# --------------------------------------------------------------------------
# Report body
# --------------------------------------------------------------------------
def build(stats, meta, include_cover=True):
    """Story for one period. With include_cover=False the cover page is
    omitted, so the section can be embedded in the combined report."""
    s = build_styles()
    os.makedirs(CHART_DIR, exist_ok=True)
    story = []

    months = month_axis(stats)
    names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
             "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    def pretty(m):
        y, mm = m.split("-")
        return f"{names[int(mm) - 1]} {y}"

    data_span = f"{pretty(months[0])} – {pretty(months[-1])}" if months else "n/a"
    # The requested window is what the report is *about*; the months actually
    # carrying comments are shown separately so a gap is visible rather than
    # silently narrowing the stated period.
    span = stats.get("period_label") or data_span

    # ---------------- Cover ----------------
    if not include_cover:
        return story + _body(stats, meta, s, span, data_span, months)

    story.append(Spacer(1, 1.5 * inch))
    story.append(Paragraph("What Yonkers Residents<br/>Complain About", s["title"]))
    story.append(Spacer(1, 0.16 * inch))
    story.append(Paragraph(
        f"The leading grievances in public comments on the City of Yonkers' "
        f"official Facebook and Instagram accounts"
        f"{('<br/>' + span) if stats.get('period_label') else ''}",
        s["subtitle"]))
    story.append(Spacer(1, 0.5 * inch))

    sub = stats.get("substantive_comments", stats["total_comments_scraped"])
    cover_rows = [
        ["Period analysed", span],
        ["Months carrying comments", data_span],
        ["Comments collected", f"{stats['total_comments_scraped']:,}"],
        ["Of which substantive", f"{sub:,}"
                                 "  (excludes emoji-only and tag-only replies)"],
        ["Complaints identified", f"{stats['total_complaints']:,}"
                                  f"  ({stats['complaint_rate']}% of substantive)"],
        ["Sources", "facebook.com/cityofyonkers · instagram.com/cityofyonkers"],
        ["Prepared", datetime.utcnow().strftime("%B %d, %Y")],
    ]
    t = Table(cover_rows, colWidths=[1.7 * inch, 3.9 * inch])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), SLATE),
        ("TEXTCOLOR", (1, 0), (1, -1), NAVY),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("LINEBELOW", (0, 0), (-1, -2), 0.4, RULE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(t)
    story.append(PageBreak())
    return story + _body(stats, meta, s, span, data_span, months)


def _body(stats, meta, s, span, data_span, months):
    """Everything after the cover: methodology, ranking, trend, quotes."""
    story = []
    sub = stats.get("substantive_comments", stats["total_comments_scraped"])

    # ---------------- Methodology ----------------
    story.append(Paragraph("How this was built", s["h1"]))
    story.append(Paragraph(
        f"Public comments were collected from the City of Yonkers' official "
        f"Facebook page and Instagram account covering {span}. "
        f"Every comment was screened for grievance language — complaint markers "
        f"such as demands to fix something, reports of neglect, questions about "
        f"why a problem persists, or explicit expressions of frustration. "
        f"Comments that were purely congratulatory, informational, or off-topic "
        f"were excluded from the counts.", s["body"]))
    story.append(Paragraph(
        f"{stats['total_comments_scraped']:,} comments were collected. A large "
        f"share of any city page's replies are emoji, tags and one-word "
        f"reactions, which express no grievance either way, so the "
        f"<b>{sub:,}</b> comments carrying actual prose form the base for every "
        f"rate in this report. Of those, "
        f"<b>{stats['total_complaints']:,} ({stats['complaint_rate']}%)</b> "
        f"registered as complaints and were sorted into civic categories using "
        f"a weighted keyword classifier. A single comment can touch more than "
        f"one issue; it is counted once under its dominant theme, with "
        f"secondary themes tracked separately under &ldquo;mentions.&rdquo;",
        s["body"]))

    story.append(Paragraph("What the numbers do and don't represent", s["h2"]))
    story.append(Paragraph(
        "These are the complaints residents chose to post publicly on the "
        "city's own channels. They are a strong signal of what frustrates the "
        "engaged public, but they are not a representative survey of all "
        "Yonkers residents. Comment volume is also shaped by what the city "
        "posts about and by moderation. Read the ranking as "
        "<i>what dominates the public conversation</i>, not as a measured "
        "incidence of each problem across the city.", s["body"]))

    if meta.get("limitations"):
        story.append(Paragraph("Collection notes", s["h2"]))
        for line in meta["limitations"]:
            story.append(Paragraph(f"• {esc(line)}", s["body"]))

    vol_path = os.path.join(CHART_DIR, "volume.png")
    if chart_volume(stats, vol_path):
        story.append(KeepTogether([
            Spacer(1, 0.1 * inch),
            Paragraph("Comments sampled by month", s["h2"]),
            Image(vol_path, width=6.5 * inch, height=2.11 * inch),
        ]))

    story.append(PageBreak())

    # ---------------- Executive summary ----------------
    top10 = stats["categories"][:10]
    # Thin periods can yield fewer than ten distinct categories; say what is
    # actually shown rather than promising ten.
    story.append(Paragraph(f"The top {len(top10)} complaints", s["h1"]))
    lead = top10[0] if top10 else None
    if lead:
        top3 = ", ".join(r["category"] for r in top10[:3])
        combined = sum(r["share"] for r in top10[:3])
        story.append(Paragraph(
            f"<b>{esc(lead['category'])}</b> is the single largest source of "
            f"complaints, accounting for {lead['share']}% of every grievance "
            f"posted. The three leading themes — {esc(top3)} — together make up "
            f"{combined:.0f}% of all complaints, meaning most of what residents "
            f"raise on the city's channels concentrates in a handful of "
            f"recurring issues.", s["body"]))

    bar_path = os.path.join(CHART_DIR, "top_categories.png")
    chart_top_categories(stats, bar_path)
    story.append(Spacer(1, 0.06 * inch))
    story.append(Image(bar_path, width=6.2 * inch, height=3.85 * inch))
    story.append(Spacer(1, 0.18 * inch))

    tbl = [["#", "Complaint category", "Comments", "Share", "Avg. likes"]]
    for i, r in enumerate(top10, 1):
        tbl.append([str(i), r["category"], f"{r['count']:,}",
                    f"{r['share']}%", f"{r['avg_likes']}"])
    t = Table(tbl, colWidths=[0.35 * inch, 3.1 * inch, 0.95 * inch,
                              0.75 * inch, 0.9 * inch], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (1, 1), (1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.8),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("TEXTCOLOR", (1, 1), (1, -1), NAVY),
        ("GRID", (0, 0), (-1, -1), 0.3, RULE),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(KeepTogether(t))
    story.append(PageBreak())

    # ---------------- Trend ----------------
    trend_path = os.path.join(CHART_DIR, "trend.png")
    if chart_trend(stats, trend_path):
        story.append(Paragraph("How the top issues moved over time", s["h1"]))
        story.append(Paragraph(
            "Monthly complaint counts for the five largest categories. Peaks "
            "follow a specific triggering event — a snowstorm, a violent "
            "incident, a budget vote — that pulls a burst of comment traffic "
            "onto the city's posts.", s["body"]))
        story.append(Paragraph(
            "<b>Read month-to-month movement with care.</b> These lines track "
            "how much was sampled as much as how much was said — a month with "
            "few sampled comments cannot produce many complaints. Check the "
            "sampling volume on the methodology page before reading any swing "
            "as a real change in resident sentiment.", s["body"]))
        story.append(Image(trend_path, width=6.6 * inch, height=3.12 * inch))
        story.append(Spacer(1, 0.16 * inch))

    # ---------------- Category detail ----------------
    story.append(Paragraph("The complaints in residents' own words", s["h1"]))
    story.append(Paragraph(
        "Each category below shows its rank, volume, and a selection of "
        "verbatim comments. Quotes are reproduced as posted, including "
        "spelling and punctuation. Commenter names are omitted.", s["body"]))
    story.append(Spacer(1, 0.1 * inch))

    for i, row in enumerate(top10, 1):
        story.append(category_block(row, i, s, months))

    # ---------------- Appendix ----------------
    story.append(PageBreak())
    story.append(Paragraph("Full category ranking", s["h1"]))
    rows = [["#", "Category", "Primary", "Mentions", "Share"]]
    for i, r in enumerate(stats["categories"], 1):
        rows.append([str(i), r["category"], f"{r['count']:,}",
                     f"{r['mentions']:,}", f"{r['share']}%"])
    t = Table(rows, colWidths=[0.35 * inch, 3.1 * inch, 0.85 * inch,
                               0.9 * inch, 0.85 * inch], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), SLATE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.3, RULE),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.16 * inch))
    story.append(Paragraph(
        "&ldquo;Primary&rdquo; counts comments whose dominant theme is that "
        "category. &ldquo;Mentions&rdquo; counts every comment that raises the "
        "issue at all, including alongside another complaint, so mentions "
        "exceed primary counts for issues that travel together.", s["small"]))

    return story


def category_block(row, rank, s, months):
    """One category: header band, stats, sparkline, and verbatim quotes."""
    spark_path = os.path.join(CHART_DIR, f"spark_{rank}.png")
    has_spark = chart_category_spark(row, spark_path, months)

    plat = row.get("by_platform", {})
    plat_str = " · ".join(
        f"{k.title()} {v:,}" for k, v in sorted(plat.items(), key=lambda kv: -kv[1]))

    header_cells = [[
        Paragraph(f"{rank}", s["rank_num"]),
        Paragraph(
            f"{esc(row['category'])}<br/>"
            f"<font size=9 color='#3E5C76'>"
            f"{row['count']:,} complaints · {row['share']}% of all complaints"
            f"{(' · ' + plat_str) if plat_str else ''}</font>",
            s["cat_title"]),
        Image(spark_path, width=1.5 * inch, height=0.36 * inch) if has_spark else "",
    ]]
    header = Table(header_cells, colWidths=[0.5 * inch, 4.4 * inch, 1.6 * inch])
    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (0, 0), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, -1), 1.1, ACCENT),
    ]))

    block = [Spacer(1, 0.16 * inch), header, Spacer(1, 0.09 * inch)]

    for ex in row["examples"][:4]:
        block.append(Paragraph(f"&ldquo;{esc(ex['text'])}&rdquo;", s["quote"]))
        bits = []
        if ex.get("platform"):
            bits.append(ex["platform"].title())
        if ex.get("year"):
            bits.append(str(ex["year"]))
        if ex.get("likes"):
            bits.append(f"{ex['likes']} likes")
        if ex.get("post_text"):
            snippet = ex["post_text"].replace("\n", " ").strip()
            if snippet:
                bits.append(f"on: &ldquo;{esc(snippet[:90])}…&rdquo;")
        block.append(Paragraph(" · ".join(bits), s["quote_meta"]))

    return KeepTogether(block)


def main(stats_name="stats.json", pdf_name=None, meta_name="meta.json"):
    with open(os.path.join(OUT_DIR, stats_name), encoding="utf-8") as fh:
        stats = json.load(fh)

    meta_path = os.path.join(OUT_DIR, meta_name)
    meta = {}
    if os.path.exists(meta_path):
        with open(meta_path, encoding="utf-8") as fh:
            meta = json.load(fh)

    out_path = os.path.join(
        OUT_DIR, pdf_name or "Yonkers_Social_Media_Complaint_Report.pdf")

    # Keep each period's charts in their own directory so a run does not
    # overwrite the previous period's images, and they stay inspectable.
    global CHART_DIR
    key = stats.get("period_key")
    CHART_DIR = os.path.join(OUT_DIR, "charts", key or "all")
    os.makedirs(CHART_DIR, exist_ok=True)

    label = stats.get("period_label")
    title = "What Yonkers Residents Complain About"
    doc = SimpleDocTemplate(
        out_path, pagesize=LETTER,
        leftMargin=0.75 * inch, rightMargin=0.75 * inch,
        topMargin=0.85 * inch, bottomMargin=0.75 * inch,
        title=f"{title} — {label}" if label else title,
        author="Social Media Listening Analysis",
        subject="Top 10 complaints in comments on City of Yonkers social media")

    decorate = make_page_decorator(f"{title} · {label}" if label else title)
    doc.build(build(stats, meta), onFirstPage=decorate, onLaterPages=decorate)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--all-periods", action="store_true",
                    help="render one report per configured reporting period")
    args = ap.parse_args()

    if args.all_periods:
        for p in PERIODS:
            stats_file = os.path.join(OUT_DIR, f"stats_{p['key']}.json")
            if not os.path.exists(stats_file):
                print(f"skipping {p['label']}: no stats file")
                continue
            main(stats_name=f"stats_{p['key']}.json",
                 pdf_name=f"Yonkers_Complaints_{p['key']}.pdf",
                 meta_name=f"meta_{p['key']}.json")
    else:
        main()
