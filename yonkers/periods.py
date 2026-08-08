"""The reporting periods, shared by the analysis and reporting steps.

Each period is a half-open date window [start, end): a comment dated on
`start` is included, one dated on `end` is not.
"""

PERIODS = [
    {"key": "2021", "label": "March – November 2021",
     "start": "2021-03-01", "end": "2021-12-01"},
    {"key": "2022", "label": "March – November 2022",
     "start": "2022-03-01", "end": "2022-12-01"},
    {"key": "2023", "label": "March – November 2023",
     "start": "2023-03-01", "end": "2023-12-01"},
    {"key": "2024", "label": "March – November 2024",
     "start": "2024-03-01", "end": "2024-12-01"},
    {"key": "2025", "label": "March – November 2025",
     "start": "2025-03-01", "end": "2025-12-01"},
    {"key": "2026", "label": "March – July 2026",
     "start": "2026-03-01", "end": "2026-08-01"},
]

BY_KEY = {p["key"]: p for p in PERIODS}


def in_period(iso_date, period):
    """True when an ISO date string falls inside the period window."""
    if not iso_date:
        return False
    day = str(iso_date)[:10]
    return period["start"] <= day < period["end"]
