# chief

Two independent single-file web apps. No build step, no server — open the HTML
file (or host it anywhere static) and go.

## C.H.I.E.F. — `index.html`

Voice-driven personal command system for John Rubbo: tap-to-speak orb, wake
word, spoken responses. Handles personal life — finances, schedule, family,
tasks.

## CFO Dashboard — `cfo.html`

A financial dashboard for **Yonkers Brewing Co**. Its own product, unrelated
to C.H.I.E.F. in look and operation:

- **KPI strip** — cash on hand, runway (from your 3-month average burn), last
  month's net, A/R outstanding, obligations due in the next 30 days
- **Cash flow** — monthly taproom / distribution / events revenue vs.
  expenses, with chart and net per month
- **Receivables** — open invoices with aging status (overdue / due soon)
- **Bills & obligations** — payables, TTB filings, rent, loan payments, sorted
  by deadline
- **Margins by beer** — price vs. cost per SKU with margin %
- **Analyst** — ask questions in plain English; every number on the page is
  sent as context so answers use your real figures (requires an Anthropic API
  key, stored only on-device)
- **Export / import** — JSON backup of all data from Settings

All data lives in the browser's local storage. Nothing is transmitted anywhere
except Analyst questions, which go directly to Anthropic's API.

> The CFO dashboard is a planning and analysis aid, not a licensed accountant.
> Confirm tax and legal matters with the brewery's accountant.
