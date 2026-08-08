"""Civic complaint taxonomy for City of Yonkers social media comments.

Each category carries weighted regex patterns. A comment can match several
categories; the highest-scoring one becomes its primary category and the rest
are kept as secondary tags. Patterns are deliberately literal and auditable so
that any number in the report can be traced back to the phrases that produced
it.

Weights:
    3  unambiguous for this category ("pothole", "shooting")
    2  strong but shared with a neighbouring category ("speeding", "landlord")
    1  weak signal, only meaningful alongside a complaint marker ("street")
"""

import re

# --------------------------------------------------------------------------
# Complaint detection
# --------------------------------------------------------------------------
# A comment counts as a complaint when it carries at least one grievance
# marker. This keeps congratulatory and purely informational comments (a large
# share of any city page's replies) out of the denominator.

COMPLAINT_MARKERS = [
    # direct negative judgement
    r"\bdisgrace(?:ful)?\b", r"\bshame(?:ful)?\b", r"\bembarrass(?:ing|ment)\b",
    r"\bridiculous\b", r"\bpathetic\b", r"\bunacceptable\b", r"\bhorrible\b",
    r"\bterrible\b", r"\bawful\b", r"\bworst\b", r"\bjoke\b", r"\bnonsense\b",
    r"\bnasty\b", r"\bfilthy\b", r"\bdisgusting\b", r"\bmess\b", r"\bgarbage\b",
    # demands / imperatives
    r"\bfix\b", r"\bdo something\b", r"\bclean\s?up\b", r"\bneeds? to be\b",
    r"\bshould be\b", r"\bstop\b", r"\benforce\b", r"\bplease\s+(?:fix|do|help)\b",
    r"\bwhen (?:will|are|is)\b", r"\bwhy (?:is|are|isn'?t|aren'?t|hasn'?t|don'?t|doesn'?t|can'?t)\b",
    r"\bhow (?:about|come)\b", r"\bwhat about\b",
    # neglect / inaction
    r"\bnothing (?:is|has|gets?|ever)\b", r"\bno one\b", r"\bnobody\b",
    r"\bstill (?:waiting|not|no|haven'?t|hasn'?t)\b", r"\bnever\b",
    r"\bignored?\b", r"\bneglect(?:ed|ing)?\b", r"\bfor years\b", r"\byears? now\b",
    r"\bevery ?day\b", r"\bagain and again\b", r"\bover and over\b",
    r"\bfall(?:ing|s)? apart\b", r"\bfalling apart\b",
    # money / trust
    r"\btax(?:es|payer)?s? (?:dollars?|money|going|paying|pay)\b",
    r"\bwhere (?:is|are|does) (?:the|our|my)\b",
    r"\bwaste (?:of|d)\b", r"\bcorrupt(?:ion)?\b", r"\bcrooked\b",
    r"\bdo(?:es)? ?n'?t care\b", r"\bcare(?:s)? (?:about )?(?:nothing|less)\b",
    r"\ball talk\b", r"\bphoto ?op\b", r"\blip service\b", r"\bempty promises?\b",
    r"\bpromised?\b.{0,30}\bnothing\b",
    # complaint framing
    r"\bcomplain(?:ed|ing|t|ts)\b", r"\bcalled\b.{0,40}\b(?:no|never|nothing)\b",
    r"\bsick (?:and tired )?of\b", r"\btired of\b", r"\bfed up\b",
    r"\benough\b", r"\bunsafe\b", r"\bdangerous\b", r"\bhazard(?:ous)?\b",
]

COMPLAINT_RE = [re.compile(p, re.I) for p in COMPLAINT_MARKERS]

# Comments that are purely positive get excluded even if a marker fires
# (e.g. "stop it, this is great"). Checked only when no other marker is strong.
PRAISE_MARKERS = [
    r"\bthank you\b", r"\bthanks\b", r"\bcongratulat", r"\bgreat job\b",
    r"\bwell done\b", r"\bawesome\b", r"\bbeautiful\b", r"\blove (?:this|it)\b",
    r"\bproud\b", r"\bexcellent\b", r"\bamazing\b", r"\bbless\b",
]
PRAISE_RE = [re.compile(p, re.I) for p in PRAISE_MARKERS]


# --------------------------------------------------------------------------
# Categories
# --------------------------------------------------------------------------

CATEGORIES = {
    "Roads & Potholes": [
        (r"\bpot ?holes?\b", 3),
        (r"\brepav(?:e|ed|ing)\b", 3),
        (r"\bpav(?:e|ed|ing|ement)\b", 2),
        (r"\bresurfac(?:e|ed|ing)\b", 3),
        (r"\bcrater\b", 3),
        (r"\broad(?:s)? (?:condition|are|is|need|repair)", 3),
        (r"\bstreet(?:s)? (?:are|is|need|repair|condition)", 2),
        (r"\basphalt\b", 2),
        (r"\bsidewalks?\b", 2),
        (r"\bcurb(?:s|ing)?\b", 2),
        (r"\bmanhole\b", 2),
        (r"\bpav(?:ing)? ?(?:job|crew)\b", 2),
        (r"\bpatch(?:ed|ing|work)?\b", 2),
        (r"\bpaving season\b", 3),
        (r"\bdirt road\b", 3),
        (r"\bthird world\b", 1),
    ],
    "Crime & Public Safety": [
        (r"\bshoot(?:ing|ings|er|out)\b", 3),
        (r"\bshot\b", 2),
        (r"\bmurder(?:s|ed)?\b", 3),
        (r"\bhomicid(?:e|es)\b", 3),
        (r"\bstabb(?:ed|ing)\b", 3),
        (r"\bgun(?:s|fire|shots?|violence)?\b", 3),
        (r"\bviolen(?:ce|t)\b", 3),
        (r"\brobb(?:ed|ery|eries)\b", 3),
        (r"\bmugg(?:ed|ing)\b", 3),
        (r"\bburglar(?:y|ies|ized)\b", 3),
        (r"\bassault(?:ed)?\b", 3),
        (r"\bgangs?\b", 3),
        (r"\bdrug(?:s|dealing|dealers?)\b", 3),
        (r"\bcrime\b", 3),
        (r"\bcriminals?\b", 3),
        (r"\bunsafe\b", 2),
        (r"\bafraid\b", 2),
        (r"\bscared\b", 2),
        (r"\bpolice\b", 2),
        (r"\bcops?\b", 2),
        (r"\bypd\b", 2),
        (r"\bprecinct\b", 2),
        (r"\bpatrol(?:s|ling)?\b", 2),
        (r"\bstolen\b", 2),
        (r"\bcar (?:theft|break ?in|jack)", 3),
        (r"\bcatalytic converter\b", 3),
        (r"\bloiter(?:ing)?\b", 2),
    ],
    "Traffic, Speeding & Reckless Driving": [
        (r"\bspeed(?:ing|ers?)\b", 3),
        (r"\breckless\b", 3),
        (r"\bdirt ?bikes?\b", 3),
        (r"\batv(?:s)?\b", 3),
        (r"\bquads?\b", 2),
        (r"\bmoped(?:s)?\b", 2),
        (r"\bstop sign\b", 3),
        (r"\bred light(?:s)?\b", 3),
        (r"\brun(?:ning|s)? (?:the )?(?:red|light|stop)", 3),
        (r"\bdrag racing\b", 3),
        (r"\bracing\b", 2),
        (r"\btraffic\b", 2),
        (r"\bcongestion\b", 2),
        (r"\bgridlock\b", 3),
        (r"\bspeed bump(?:s)?\b", 3),
        (r"\bspeed hump(?:s)?\b", 3),
        (r"\bcrosswalks?\b", 2),
        (r"\bpedestrian(?:s)?\b", 2),
        (r"\bhit (?:by|and run)\b", 3),
        (r"\btraffic light(?:s)?\b", 3),
        (r"\bblow(?:ing|s)? (?:through|past)\b", 2),
        (r"\bdouble ?park(?:ed|ing)\b", 2),
        (r"\bno enforcement\b", 2),
    ],
    "Parking": [
        (r"\bparking\b", 3),
        (r"\bparked\b", 2),
        (r"\bmeter(?:s|ed)?\b", 2),
        (r"\bticket(?:s|ed|ing)\b", 2),
        (r"\btow(?:ed|ing)\b", 3),
        (r"\bpermit(?:s)? park", 3),
        (r"\balternate side\b", 3),
        (r"\bno ?where to park\b", 3),
        (r"\bparking (?:spot|space|garage|lot)", 3),
        (r"\bmunimeter\b", 3),
        (r"\bboot(?:ed|ing)\b", 2),
    ],
    "Taxes & Cost of Living": [
        (r"\btax(?:es|ation)?\b", 3),
        (r"\bproperty tax\b", 3),
        (r"\bschool tax\b", 3),
        (r"\btax(?:payer)?s?\b", 2),
        (r"\brais(?:e|ed|ing) (?:our |the |my )?tax", 3),
        (r"\bassessment(?:s)?\b", 2),
        (r"\breassess", 3),
        (r"\bwater bill(?:s)?\b", 3),
        (r"\bafford(?:able|ability)?\b", 2),
        (r"\bcost of living\b", 3),
        (r"\bexpensive\b", 2),
        (r"\bbudget\b", 2),
        (r"\bfee(?:s)?\b", 2),
        (r"\bsurcharge\b", 3),
        (r"\bmov(?:e|ing|ed) out\b", 2),
        (r"\bleav(?:e|ing) yonkers\b", 2),
        (r"\bpriced out\b", 3),
        (r"\brent (?:is|too|so) (?:high|much|expensive)", 3),
    ],
    "Schools & Education": [
        (r"\bschool(?:s)?\b", 3),
        (r"\bstudent(?:s)?\b", 2),
        (r"\bteacher(?:s)?\b", 2),
        (r"\bclassroom(?:s)?\b", 3),
        (r"\bovercrowd(?:ed|ing)\b", 3),
        (r"\bboe\b", 3),
        (r"\bboard of ed", 3),
        (r"\byonkers public schools\b", 3),
        (r"\bschool board\b", 3),
        (r"\bcurriculum\b", 3),
        (r"\bgraduation rate\b", 3),
        (r"\bpupil(?:s)?\b", 2),
        (r"\bschool bus(?:es)?\b", 3),
        (r"\btrailer(?:s)? (?:for|at) school", 3),
        (r"\bportable classroom", 3),
        (r"\beducation\b", 2),
    ],
    "Trash, Sanitation & Illegal Dumping": [
        (r"\btrash\b", 3),
        (r"\bgarbage\b", 3),
        (r"\brubbish\b", 3),
        (r"\blitter(?:ing|ed)?\b", 3),
        (r"\bdump(?:ing|ed|ers?)\b", 3),
        (r"\bsanitation\b", 3),
        (r"\brecycl(?:e|ing)\b", 3),
        (r"\bpick ?up\b", 2),
        (r"\brats?\b", 3),
        (r"\brodent(?:s)?\b", 3),
        (r"\broaches?\b", 3),
        (r"\bvermin\b", 3),
        (r"\bmattress(?:es)?\b", 3),
        (r"\bdebris\b", 2),
        (r"\bdirty\b", 2),
        (r"\bfilth(?:y)?\b", 2),
        (r"\bbulk (?:pick|item)", 3),
        (r"\bcans? (?:not|never) (?:picked|emptied)", 3),
        (r"\bovergrown\b", 2),
        (r"\bweeds?\b", 2),
    ],
    "Housing & Overdevelopment": [
        (r"\bdevelop(?:ment|ers?|ing)\b", 3),
        (r"\bover ?develop", 3),
        (r"\bluxury\b", 3),
        (r"\bhigh ?rise(?:s)?\b", 3),
        (r"\bcondo(?:s|minium)?\b", 3),
        (r"\bapartment(?:s)? (?:building|complex)", 3),
        (r"\baffordable housing\b", 3),
        (r"\blandlord(?:s)?\b", 3),
        (r"\btenant(?:s)?\b", 3),
        (r"\bevict(?:ed|ion|ions)\b", 3),
        (r"\bsection 8\b", 3),
        (r"\bhousing\b", 2),
        (r"\bzoning\b", 3),
        (r"\bbuilding(?:s)? going up\b", 3),
        (r"\bmore (?:apartments|buildings|units)\b", 3),
        (r"\bgentrif", 3),
        (r"\bslumlord(?:s)?\b", 3),
        (r"\bcode violation", 3),
    ],
    "Snow, Flooding & Storm Response": [
        (r"\bsnow\b", 3),
        (r"\bplow(?:ed|ing|s)?\b", 3),
        (r"\bsalt(?:ed|ing)?\b", 2),
        (r"\bblizzard\b", 3),
        (r"\bstorm\b", 2),
        (r"\bflood(?:ed|ing|s)?\b", 3),
        (r"\bdrain(?:s|age|ed)?\b", 3),
        (r"\bsewer(?:s)? back", 3),
        (r"\bcatch basin\b", 3),
        (r"\bice(?:d|y)?\b", 2),
        (r"\bpower (?:out|outage)", 3),
        (r"\bcon ?ed(?:ison)?\b", 2),
        (r"\bdown(?:ed)? (?:tree|wire|line)", 3),
        (r"\bunplowed\b", 3),
    ],
    "City Responsiveness & Accountability": [
        (r"\b311\b", 3),
        (r"\bcall(?:ed|ing)? (?:the )?city\b", 3),
        (r"\bno (?:one|body) (?:answers?|responds?|calls?|came|shows?)", 3),
        (r"\bnever (?:answer|respond|call|came|show)", 3),
        (r"\bwork order\b", 3),
        (r"\bcomplain(?:ed|ing|t|ts)\b", 2),
        (r"\bmayor\b", 2),
        (r"\bspano\b", 2),
        (r"\bcity hall\b", 3),
        (r"\bcouncil(?:man|woman|member)?\b", 2),
        (r"\bcorrupt(?:ion)?\b", 3),
        (r"\bpatronage\b", 3),
        (r"\bnepotism\b", 3),
        (r"\bphoto ?op\b", 3),
        (r"\ball talk\b", 3),
        (r"\bempty promises?\b", 3),
        (r"\btransparen(?:t|cy)\b", 3),
        (r"\baccountab(?:le|ility)\b", 3),
        (r"\bdo(?:es)? ?n'?t care\b", 2),
        (r"\bignore(?:d|s)?\b", 2),
        (r"\bpress release\b", 2),
        (r"\bre ?elect", 2),
        (r"\bvote (?:him|them|her) out\b", 3),
    ],
    "Parks & Public Spaces": [
        (r"\bpark(?:s)? (?:are|is|need|condition|maintenance)", 3),
        (r"\bplayground(?:s)?\b", 3),
        (r"\bball ?field(?:s)?\b", 3),
        (r"\bbasketball court", 3),
        (r"\btennis court", 3),
        (r"\bpool(?:s)?\b", 2),
        (r"\brec(?:reation)? center\b", 3),
        (r"\btrail(?:s)?\b", 2),
        (r"\bwaterfront\b", 2),
        (r"\bbench(?:es)?\b", 2),
        (r"\bgrass\b", 2),
        (r"\bmow(?:ed|ing|n)?\b", 2),
    ],
    "Street Lighting & Infrastructure": [
        (r"\bstreet ?light(?:s|ing)?\b", 3),
        (r"\blight(?:s)? (?:are|is)? ?(?:out|broken|not working)", 3),
        (r"\bdark\b", 1),
        (r"\bhydrant(?:s)?\b", 3),
        (r"\bwater main\b", 3),
        (r"\bsign(?:s|age)?\b", 2),
        (r"\bguard ?rail\b", 3),
        (r"\bbridge\b", 2),
        (r"\bstairs?\b", 2),
        (r"\butilit(?:y|ies)\b", 2),
        (r"\bwires?\b", 2),
    ],
    "Homelessness & Quality of Life": [
        (r"\bhomeless(?:ness)?\b", 3),
        (r"\bpanhandl(?:e|ing|ers?)\b", 3),
        (r"\bencampment(?:s)?\b", 3),
        (r"\bnoise\b", 3),
        (r"\bloud music\b", 3),
        (r"\bfireworks?\b", 3),
        (r"\bquality of life\b", 3),
        (r"\bmental health\b", 2),
        (r"\bopen ?air drug\b", 3),
        (r"\bpublic (?:urinat|drink)", 3),
        (r"\bshelter(?:s)?\b", 2),
    ],
}

CATEGORY_RE = {
    name: [(re.compile(p, re.I), w) for p, w in pats]
    for name, pats in CATEGORIES.items()
}


def is_complaint(text: str) -> bool:
    """True when the comment carries at least one grievance marker.

    A comment that fires only praise markers and a single weak grievance
    marker is treated as praise, which keeps "stop it, this is amazing"
    style replies out of the counts.
    """
    if not text:
        return False
    hits = sum(1 for r in COMPLAINT_RE if r.search(text))
    if hits == 0:
        return False
    praise = sum(1 for r in PRAISE_RE if r.search(text))
    return hits > praise


def score_categories(text: str) -> dict:
    """Return {category: score} for every category with at least one match."""
    scores = {}
    if not text:
        return scores
    for name, pats in CATEGORY_RE.items():
        total = 0
        for rx, weight in pats:
            if rx.search(text):
                total += weight
        if total:
            scores[name] = total
    return scores


def classify(text: str):
    """Return (primary_category, secondary_categories, scores).

    primary is None when nothing matched.
    """
    scores = score_categories(text)
    if not scores:
        return None, [], {}
    ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
    primary = ranked[0][0]
    secondary = [n for n, _ in ranked[1:] if _ >= 3]
    return primary, secondary, scores
