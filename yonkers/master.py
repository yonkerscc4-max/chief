"""Render the master document: findings and policy agenda in one file.

Combines what the listening exercise found with what to do about it:

    cover -> executive summary -> methodology -> findings -> agenda

Findings use the pooled six-window dataset (season-matched, so nothing is
an artifact of which months were sampled). The agenda section reuses the
same tagline-and-policy content as the standalone agenda document.
"""

import json
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer,
    Table, TableStyle,
)

import agenda as A
import report as R

OUT_DIR = R.OUT_DIR


def section_title(text, subtitle, s):
    return [Spacer(1, 2.5 * inch),
            Paragraph(text, s["title"]),
            Spacer(1, 0.12 * inch),
            Paragraph(subtitle, s["subtitle"]),
            PageBreak()]


def build_master():
    s = R.build_styles()
    with open(os.path.join(OUT_DIR, "stats_windows.json"), encoding="utf-8") as fh:
        win = json.load(fh)
    with open(os.path.join(OUT_DIR, "stats.json"), encoding="utf-8") as fh:
        allst = json.load(fh)
    meta_path = os.path.join(OUT_DIR, "meta_windows.json")
    meta = {}
    if os.path.exists(meta_path):
        with open(meta_path, encoding="utf-8") as fh:
            meta = json.load(fh)

    story = []

    # ---------------- Cover ----------------
    story.append(Spacer(1, 1.4 * inch))
    story.append(Paragraph("What Yonkers Residents Complain About<br/>"
                           "— and What to Do About It", s["title"]))
    story.append(Spacer(1, 0.18 * inch))
    story.append(Paragraph(
        "Findings from 9,697 public comments on the City of Yonkers' official "
        "Facebook and Instagram accounts, and a policy agenda drawn from them",
        s["subtitle"]))
    story.append(Spacer(1, 0.5 * inch))
    rows = [
        ["Evidence base", "9,697 comments · 2021 – 2026 · Facebook and Instagram"],
        ["Findings drawn from", "The six season-matched windows: 7,081 comments, "
                                "503 complaints"],
        ["Issues identified", "14 civic categories"],
        ["Policies proposed", "70 — five per issue, short and long term"],
        ["Sources", "facebook.com/cityofyonkers · instagram.com/cityofyonkers"],
    ]
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

    # ---------------- Executive summary ----------------
    story.append(Paragraph("Executive summary", s["h1"]))
    top = win["categories"]
    lead = ", ".join(r["category"] for r in top[:4])
    four = sum(r["share"] for r in top[:4])

    story.append(Paragraph(
        f"Residents post a great deal on the city's channels, and most of it "
        f"is not complaint: of {win['substantive_comments']:,} comments "
        f"carrying actual prose, {win['total_complaints']:,} "
        f"({win['complaint_rate']}%) register as grievances. What those "
        f"grievances concentrate on is remarkably stable.", s["body"]))
    story.append(Paragraph(
        f"<b>Four themes carry {four:.0f}% of every complaint:</b> "
        f"{R.esc(lead)}. These are not event-driven spikes — they appear at or "
        f"near the top of every period examined from 2021 to 2026. The issues "
        f"that come and go (potholes, jobs, parking) tend to track what the "
        f"city posted about that year rather than a shift in what residents "
        f"care about.", s["body"]))
    story.append(Paragraph(
        "The single most striking pattern is that the top of the list is not "
        "about any one service failing. It is about the city as an "
        "institution: whether anyone answers, and whether the money is "
        "accounted for. Residents raise responsiveness and taxes more than "
        "they raise crime, potholes and housing combined.", s["body"]))

    story.append(Paragraph("The cheapest fix available", s["h2"]))
    story.append(Paragraph(
        "One operational contradiction runs through three of the top issues at "
        "once. Residents are ticketed under alternate-side parking rules on "
        "streets the city never actually cleaned, and charged at meters on "
        "blocks where parking is suspended for snow. Fixing that — enforcement "
        "follows the sweeper, not the calendar — costs a policy memo rather "
        "than a capital budget, and defuses complaints across snow response, "
        "parking and city responsiveness simultaneously.", s["body"]))

    story.append(Paragraph("How to read the two numbers in this document", s["h2"]))
    story.append(Paragraph(
        f"Findings here use the six season-matched windows (March–November "
        f"2021–2025 and March–July 2026): {win['total_complaints']:,} "
        f"complaints. A separate pooled view of every comment collected, "
        f"including December through February, yields "
        f"{allst['total_complaints']:,} complaints and puts snow and storm "
        f"response first. Both are correct. The season-matched view is used "
        f"for the findings because it cannot be distorted by which months "
        f"happened to be sampled.", s["body"]))
    story.append(PageBreak())

    # ---------------- Findings ----------------
    story.extend(section_title(
        "Part One: The Findings",
        "What residents actually complain about, in their own words", s))
    story.extend(R.build(win, meta, include_cover=False))
    story.append(PageBreak())

    # ---------------- Agenda ----------------
    story.extend(section_title(
        "Part Two: The Agenda",
        "A tagline and five policies for each of the fourteen issues", s))
    story.extend(A.build_story(win))

    return story


def main():
    out_path = os.path.join(OUT_DIR, "Yonkers_Findings_and_Agenda.pdf")
    doc = SimpleDocTemplate(
        out_path, pagesize=LETTER,
        leftMargin=0.75 * inch, rightMargin=0.75 * inch,
        topMargin=0.85 * inch, bottomMargin=0.75 * inch,
        title="What Yonkers Residents Complain About - and What to Do About It",
        author="Social Media Listening Analysis",
        subject="Complaint findings and a policy agenda for the City of Yonkers")
    decorate = R.make_page_decorator(
        "What Yonkers Residents Complain About · Findings and Agenda")
    doc.build(build_master(), onFirstPage=decorate, onLaterPages=decorate)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
