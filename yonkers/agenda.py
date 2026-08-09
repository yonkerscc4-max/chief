"""Render the policy agenda: a tagline and five policies per complaint issue.

Reads output/stats.json for the issue ranking and volumes, and pairs each
issue with a campaign-style tagline, a verbatim resident quote, and five
policies tagged short or long term.

The policy text is drafted from what residents actually raised in the
scraped comments - the specific streets, parks, fees and rules they named -
rather than generic municipal boilerplate.
"""

import json
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.platypus import (
    KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
    TableStyle,
)

import report as R

OUT_DIR = R.OUT_DIR
SHORT, LONG = "SHORT", "LONG"

# Each issue: tagline, a verbatim resident line, and five policies.
AGENDA = [
    {
        "issue": "Snow, Flooding & Storm Response",
        "tagline": "Plow Every Street, Not Just the Main Ones",
        "quote": "Side streets are icy, dangerous, and barely passable… "
                 "Yonkers has many many hills.",
        "policies": [
            (SHORT, "Pre-treat the hills before the first flake",
             "Publish a named list of steep-grade streets that get brined "
             "ahead of every forecast storm, and post completion times so "
             "residents can see it happened."),
            (SHORT, "Publish a live plow map",
             "GPS on every plow, feeding a public map showing when each street "
             "was last cleared. This ends the argument about whether a street "
             "was skipped."),
            (SHORT, "Never ticket a street the city hasn't cleaned",
             "Suspend alternate-side enforcement on any block that has not yet "
             "been plowed curb to curb, and void tickets issued on uncleaned "
             "streets automatically."),
            (LONG, "Buy snow melters for the dense corridors",
             "Residents proposed this directly. Melters let crews remove snow "
             "from narrow streets with nowhere to pile it, instead of pushing "
             "it into parked cars and crosswalks."),
            (LONG, "Rebuild drainage where flooding repeats",
             "Map every block that floods more than once in three years and "
             "put catch-basin and storm-sewer upgrades on a funded, published "
             "schedule."),
        ],
    },
    {
        "issue": "City Responsiveness & Accountability",
        "tagline": "Every Complaint Gets a Number",
        "quote": "Financial accountability. What does the city do with the "
                 "funds they grab from tax payers?",
        "policies": [
            (SHORT, "A real 311 with a tracking number",
             "Every report gets a case number, an owner, and a status the "
             "resident can check without calling back."),
            (SHORT, "Publish response times by department and district",
             "A monthly scorecard showing how long each department takes to "
             "close cases, broken out by neighbourhood so no district is "
             "quietly served last."),
            (SHORT, "Answer the channels the city actually posts on",
             "Staff the comment threads. A large share of these complaints are "
             "questions the city never answered in the place they were asked."),
            (LONG, "Put the checkbook online",
             "A searchable register of contracts, vendors and payments over a "
             "set threshold, updated monthly. The corruption complaints here "
             "are mostly complaints about not being able to see anything."),
            (LONG, "Independent inspector general",
             "An office outside the mayor's control, with subpoena power and "
             "published findings, to investigate procurement and hiring."),
        ],
    },
    {
        "issue": "Taxes & Cost of Living",
        "tagline": "End the Yonkers Surcharge",
        "quote": "When will the income tax surcharge be eliminated? "
                 "You are bankrupting the citizens of Yonkers.",
        "policies": [
            (SHORT, "Publish a plain-language tax receipt",
             "Every property owner gets a one-page breakdown of where their "
             "money went, by service, each year."),
            (SHORT, "Expand and auto-enrol senior and veteran exemptions",
             "Most people who qualify never apply. Use records the city "
             "already holds to enrol them and backdate the relief."),
            (LONG, "Phase out the resident income tax surcharge",
             "Set a multi-year schedule to retire the surcharge, funded by "
             "growth in the commercial tax base rather than a service cut."),
            (LONG, "Grow the commercial base deliberately",
             "Tie development approvals to net new commercial ratables, so new "
             "buildings widen the tax base instead of shifting the burden onto "
             "existing homeowners."),
            (LONG, "Independent reassessment on a fixed cycle",
             "Regular, transparent reassessment stops the slow drift that "
             "leaves long-time owners paying a premium over recent buyers."),
        ],
    },
    {
        "issue": "Schools & Education",
        "tagline": "Build Schools, Not Just Buildings",
        "quote": "It is great more housing is being built, but where are the "
                 "children going to go to school?",
        "policies": [
            (SHORT, "Publish a school-capacity map beside every project",
             "No residential approval moves without the enrolment impact for "
             "the receiving schools printed in the public file."),
            (SHORT, "Get the trailers out of use first",
             "Fund and publish a dated plan to retire portable classrooms, "
             "starting with the most overcrowded schools."),
            (LONG, "A school-impact contribution on large residential projects",
             "Developments above a unit threshold contribute to classroom "
             "capacity in the district they fill."),
            (LONG, "A capital plan that tracks the housing pipeline",
             "Tie the school construction schedule to approved units, so "
             "capacity arrives with the residents rather than a decade later."),
            (LONG, "Competitive teacher pay and retention",
             "Yonkers competes with wealthier Westchester districts for the "
             "same teachers. Pay parity is the precondition for everything "
             "else on this list."),
        ],
    },
    {
        "issue": "Parking",
        "tagline": "No Ticket Without a Sweep",
        "quote": "How can alternate side be enforced when there is nowhere to "
                 "park on many streets?",
        "policies": [
            (SHORT, "Enforcement follows the sweeper, not the calendar",
             "Alternate-side tickets are only valid where cleaning actually "
             "happened that day. This is the single most repeated grievance in "
             "the data."),
            (SHORT, "Fix the meter contradiction",
             "When alternate-side is suspended for snow, suspend meter "
             "enforcement on the same blocks instead of charging for spaces "
             "nobody can reach."),
            (SHORT, "Notice before the ticket",
             "Push rule changes to text and email the evening before, and void "
             "tickets from any change announced with less than 12 hours' "
             "notice."),
            (LONG, "Residential permit parking in the squeezed neighbourhoods",
             "Where housing density outran the curb, permits give residents a "
             "realistic chance at a space near home."),
            (LONG, "Shared municipal garages in the dense corridors",
             "Build or lease structured parking so overnight demand comes off "
             "streets that cannot be cleaned while full."),
        ],
    },
    {
        "issue": "Trash, Sanitation & Illegal Dumping",
        "tagline": "Clean Streets, Every Block",
        "quote": "Every road littered with trash, every exit ramp to any "
                 "thruway, parkway or highway looks a wreck.",
        "policies": [
            (SHORT, "Free bulk pickup on demand",
             "Most illegal dumping is mattresses and furniture. Make legal "
             "disposal easier and free to schedule, and the pile-ups fall."),
            (SHORT, "Cameras and real fines at the known dumping sites",
             "Residents can already name the spots. Enforce there first and "
             "publish the results."),
            (SHORT, "Adopt the ramps and trailheads",
             "A standing clean-up schedule for highway ramps and the Old "
             "Croton Aqueduct trail, which residents raise repeatedly and "
             "which fall between agency responsibilities."),
            (LONG, "Hold large buildings to the same rules as homeowners",
             "Summonses for apartment buildings that mix recycling and refuse, "
             "with escalating penalties for repeat offenders."),
            (LONG, "Containerised collection on the dense corridors",
             "Move from loose bags to shared containers on the busiest "
             "streets, which cuts both litter and the rat population."),
        ],
    },
    {
        "issue": "Jobs, Hiring & Local Economy",
        "tagline": "Yonkers Jobs for Yonkers Residents",
        "quote": "I have a union card and can't find no work… "
                 "they only hire their own family and friends.",
        "policies": [
            (SHORT, "Post every city job in one public place",
             "One portal, every opening, with closing dates and the number of "
             "applicants. The perception of a closed shop is fed by "
             "invisibility."),
            (SHORT, "Publish hiring outcomes",
             "For each posting, report applicants, interviews and hires by "
             "residency. Transparency is the cheapest answer to patronage "
             "complaints."),
            (LONG, "Local hire requirements on subsidised projects",
             "Any project taking a tax abatement commits to a Yonkers "
             "residency share for construction and permanent jobs, with "
             "clawbacks if missed."),
            (LONG, "Apprenticeships tied to the capital programme",
             "Route residents into the trades through the city's own paving, "
             "school and sewer work."),
            (LONG, "Storefront strategy for the commercial strips",
             "Targeted help for small business on the corridors residents "
             "name, rather than incentives concentrated on the waterfront."),
        ],
    },
    {
        "issue": "Roads & Potholes",
        "tagline": "Pave It, Don't Patch It",
        "quote": "Patching a road isn't considered fixing it.",
        "policies": [
            (SHORT, "Publish the paving list before the season",
             "Every street scheduled for the year, posted in advance, with "
             "completion dates marked off as work finishes."),
            (SHORT, "Guaranteed pothole turnaround",
             "A published deadline from report to repair, with the count of "
             "missed deadlines reported monthly."),
            (SHORT, "Make utilities restore full width",
             "Require full-width repaving after utility cuts instead of the "
             "trench patches that fail within a winter."),
            (LONG, "A funded multi-year resurfacing programme",
             "Rank every street by condition and fund a rolling schedule, so "
             "reconstruction replaces perpetual patching."),
            (LONG, "Fix the crossings while you pave",
             "Rebuild crosswalks, curb ramps and sidewalks as part of each "
             "paving job, including the arterials residents call unsafe to "
             "cross on foot."),
        ],
    },
    {
        "issue": "Crime & Public Safety",
        "tagline": "Guns Off Our Blocks",
        "quote": "A 15-year-old with a gun. How does someone that young get "
                 "their hands on one?",
        "policies": [
            (SHORT, "Focused deterrence on the small number driving violence",
             "Concentrate outreach and enforcement on the individuals and "
             "blocks that account for most shootings, rather than broad sweeps."),
            (SHORT, "Fund credible-messenger violence interruption",
             "Trained community workers who can defuse retaliation before it "
             "becomes the next shooting."),
            (SHORT, "Trace every recovered firearm and publish the results",
             "Show residents where guns are actually coming from, which is the "
             "question they keep asking."),
            (LONG, "Year-round paid youth employment",
             "The comments tie youth violence to having nothing to do. Steady "
             "paid work and late-night programming is the long-term answer."),
            (LONG, "Beat officers who stay on the same blocks",
             "Consistent assignment so officers and residents know each other, "
             "instead of rotating faces after every incident."),
        ],
    },
    {
        "issue": "Housing & Overdevelopment",
        "tagline": "Affordable Means Affordable Here",
        "quote": "Hudson Piers requires tenants to make 66 times the income "
                 "for affordable housing. What a joke.",
        "policies": [
            (SHORT, "Set affordability to Yonkers incomes",
             "Peg income limits to the local median rather than a regional "
             "figure that prices out the residents the units are meant for."),
            (SHORT, "Publish every project's affordable split",
             "Unit counts, rent levels and income requirements posted plainly "
             "at approval. Residents did this arithmetic themselves - 225 "
             "market to 25 affordable - and were angry about what they found."),
            (SHORT, "One application for every affordable unit in the city",
             "A single waiting list and portal instead of per-building "
             "lotteries that reward whoever hears first."),
            (LONG, "Raise the mandatory affordable share on upzoned sites",
             "If the city grants the density, the public gets more than a "
             "token set-aside."),
            (LONG, "Permanent affordability and anti-harassment enforcement",
             "Long deed restrictions so units cannot convert to market rate, "
             "with a funded office to enforce against landlord harassment."),
        ],
    },
    {
        "issue": "Parks & Public Spaces",
        "tagline": "Every Park Playable",
        "quote": "The playground is rusted which is a hazard… unpainted "
                 "basketball court, broken glass on the courts.",
        "policies": [
            (SHORT, "Safety sweep of every playground",
             "Inspect all equipment, publish the findings, and fix or close "
             "what is hazardous - residents named rusted equipment and glass "
             "on courts specifically."),
            (SHORT, "A published maintenance standard",
             "Set mowing, litter and court-resurfacing frequencies and report "
             "against them park by park."),
            (SHORT, "Report-a-problem code on every park sign",
             "A scannable code that files a tracked case, so a broken swing "
             "does not depend on knowing whom to call."),
            (LONG, "A rolling renovation programme worst-first",
             "Rank every park by condition and renovate on a published cycle, "
             "starting with the smaller neighbourhood parks that residents say "
             "are skipped."),
            (LONG, "Equity test on parks capital spending",
             "Publish investment per resident by neighbourhood, so waterfront "
             "showpieces cannot crowd out the parks people use daily."),
        ],
    },
    {
        "issue": "Homelessness & Quality of Life",
        "tagline": "A Door for Everyone",
        "quote": "We have over 800 homeless men and women here in Yonkers.",
        "policies": [
            (SHORT, "Street outreach with a placement, not a move-along",
             "Teams that can offer a bed and a caseworker the same day."),
            (SHORT, "Enforce the noise rules people actually raise",
             "Set and enforce hours for leaf blowers and amplified sound, with "
             "a complaint route that produces a response."),
            (SHORT, "Public bathrooms and water in the busy parks",
             "Basic facilities remove a recurring quality-of-life flashpoint "
             "for everyone using the space."),
            (LONG, "Permanent supportive housing",
             "Housing paired with services is what ends chronic homelessness; "
             "shelter capacity alone recycles people through the system."),
            (LONG, "Homelessness prevention fund",
             "Emergency rent and arrears help, which is far cheaper than "
             "sheltering a family after eviction."),
        ],
    },
    {
        "issue": "Street Lighting & Infrastructure",
        "tagline": "Light Every Corner",
        "quote": "Street lights should be fixed so they actually work. Also "
                 "install new ones where there aren't, like Agar St.",
        "policies": [
            (SHORT, "Seven-day streetlight repair",
             "A published deadline from report to relight, with outages "
             "mapped publicly so nobody wonders if it was logged."),
            (SHORT, "Night audit of the dark blocks",
             "Walk the streets residents name after dark, and fill the gaps "
             "where no light was ever installed."),
            (SHORT, "Clear the sight lines",
             "Trim vegetation blocking lights and signs, and enforce against "
             "trucks parked where they block crossings and visibility."),
            (LONG, "City-wide LED conversion with smart outage reporting",
             "Fixtures that report their own failures, so repairs start before "
             "a resident has to complain."),
            (LONG, "Lighting standards in every capital project",
             "Fold pedestrian-scale lighting into paving, park and streetscape "
             "work rather than treating it as a separate ask."),
        ],
    },
    {
        "issue": "Traffic, Speeding & Reckless Driving",
        "tagline": "Slow the Streets Down",
        "quote": "Drivers always going through red lights, passing buses… "
                 "drag racing… riding on the sidewalks.",
        "policies": [
            (SHORT, "Daylight the dangerous corners",
             "Clear parking back from crossings at the intersections residents "
             "name, so drivers and pedestrians can see each other."),
            (SHORT, "Traffic calming where schools and crossings are",
             "Speed humps, raised crossings and signal timing prioritised "
             "around schools and bus stops."),
            (SHORT, "Target the dirt bikes and ATVs at the source",
             "Enforcement aimed at the sale, storage and fuelling of illegal "
             "off-road vehicles rather than street pursuits."),
            (LONG, "Redesign the arterials residents keep naming",
             "Road diets, protected crossings and median refuges on the "
             "corridors where speeding is chronic."),
            (LONG, "A published Vision Zero plan with a crash map",
             "Rank every intersection by injury history and fix them in order, "
             "reporting progress annually."),
        ],
    },
]


def build_story(stats):
    s = R.build_styles()
    volumes = {r["category"]: r for r in stats["categories"]}
    story = []

    tag = R.ParagraphStyle(
        "tag", parent=s["cat_title"], fontSize=17, leading=20,
        textColor=R.ACCENT)
    quote = R.ParagraphStyle(
        "aq", parent=s["quote"], fontSize=9, leading=12.5, leftIndent=0,
        textColor=R.SLATE)

    # ---------------- Cover ----------------
    story.append(Spacer(1, 1.5 * inch))
    story.append(Paragraph("A Policy Agenda for Yonkers", s["title"]))
    story.append(Spacer(1, 0.16 * inch))
    story.append(Paragraph(
        "A tagline and five practical policies for every issue residents "
        "raised on the City of Yonkers' social media, 2021 – 2026",
        s["subtitle"]))
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph(
        "Fourteen issues, ranked by how often residents raised them. Each "
        "carries a tagline, a line in a resident's own words, and five "
        "policies — some deliverable inside a year, some requiring a capital "
        "plan and a term of office. Policies are drafted from the specific "
        "streets, fees, parks and rules residents named, not from a generic "
        "municipal template.", s["body"]))
    story.append(Spacer(1, 0.12 * inch))
    story.append(Paragraph(
        "<b>These are proposals, not costed commitments.</b> Nothing here has "
        "been through legal review, budget scoring, or a check against what "
        "the city is already doing. Treat it as an agenda to argue with.",
        s["body"]))
    story.append(PageBreak())

    # ---------------- Tagline index ----------------
    story.append(Paragraph("The taglines at a glance", s["h1"]))
    rows = [["#", "Issue", "Tagline", "Share"]]
    for i, item in enumerate(AGENDA, 1):
        v = volumes.get(item["issue"])
        rows.append([str(i), item["issue"], item["tagline"],
                     f"{v['share']}%" if v else "—"])
    t = Table(rows, colWidths=[0.3 * inch, 2.35 * inch, 3.0 * inch, 0.65 * inch],
              repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), R.NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (2, 1), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.4),
        ("TEXTCOLOR", (2, 1), (2, -1), R.ACCENT),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (3, 0), (3, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, R.LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.3, R.RULE),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(t)
    story.append(PageBreak())

    # ---------------- One block per issue ----------------
    for i, item in enumerate(AGENDA, 1):
        v = volumes.get(item["issue"])
        head = Table([[
            Paragraph(f"{i}", s["rank_num"]),
            Paragraph(
                f"{R.esc(item['issue'])}<br/>"
                f"<font size=9 color='#3E5C76'>"
                f"{v['count']:,} complaints · {v['share']}% of all complaints"
                f"</font>" if v else R.esc(item["issue"]), s["cat_title"]),
        ]], colWidths=[0.5 * inch, 6.0 * inch])
        head.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (0, 0), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LINEBELOW", (0, 0), (-1, -1), 1.1, R.ACCENT),
        ]))

        block = [head, Spacer(1, 0.07 * inch),
                 Paragraph(f"&ldquo;{R.esc(item['tagline'])}&rdquo;", tag),
                 Spacer(1, 0.03 * inch),
                 Paragraph(f"Resident: &ldquo;{R.esc(item['quote'])}&rdquo;",
                           quote),
                 Spacer(1, 0.07 * inch)]

        prows = [["Term", "Policy"]]
        for term, title, body in item["policies"]:
            prows.append([
                term,
                Paragraph(f"<b>{R.esc(title)}</b><br/>{R.esc(body)}",
                          R.ParagraphStyle("p", parent=s["body"],
                                           fontSize=8.6, leading=11.6,
                                           spaceAfter=0)),
            ])
        pt = Table(prows, colWidths=[0.62 * inch, 5.88 * inch], repeatRows=1)
        style = [
            ("BACKGROUND", (0, 0), (-1, 0), R.SLATE),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (0, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.3, R.RULE),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
        for r, (term, _, _) in enumerate(item["policies"], 1):
            style.append(("TEXTCOLOR", (0, r), (0, r),
                          R.ACCENT if term == SHORT else R.NAVY))
        pt.setStyle(TableStyle(style))
        block.append(pt)
        story.append(KeepTogether(block))
        story.append(Spacer(1, 0.22 * inch))

    return story


def main():
    with open(os.path.join(OUT_DIR, "stats.json"), encoding="utf-8") as fh:
        stats = json.load(fh)
    out_path = os.path.join(OUT_DIR, "Yonkers_Policy_Agenda.pdf")
    doc = SimpleDocTemplate(
        out_path, pagesize=LETTER,
        leftMargin=0.75 * inch, rightMargin=0.75 * inch,
        topMargin=0.85 * inch, bottomMargin=0.75 * inch,
        title="A Policy Agenda for Yonkers",
        author="Social Media Listening Analysis",
        subject="Taglines and policies for each complaint issue")
    decorate = R.make_page_decorator("A Policy Agenda for Yonkers")
    doc.build(build_story(stats), onFirstPage=decorate, onLaterPages=decorate)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
