# C.H.I.E.F. + C.F.O.

Two voice-driven AI command systems for John Rubbo, built as single-file web apps
powered by the Anthropic API. No build step, no server — open the HTML file (or
host it anywhere static) and go.

## The systems

| App | File | Domain |
|-----|------|--------|
| **C.H.I.E.F.** — Command Hub for Intelligence, Execution and Forward-planning | `index.html` | Personal life: finances, schedule, family, tasks |
| **C.F.O.** — Cashflow · Forecasting · Operations | `cfo.html` | Yonkers Brewing Co: cash flow, P&L, margins, A/R & A/P, excise taxes, payroll |

Each app links to the other from its header.

## Features (both apps)

- **Voice in / voice out** — tap the orb to speak, responses are read aloud
- **Wake word** — optional always-on listening ("Hey Chief" / "Hey CFO", customizable)
- **Text input** — type commands when voice isn't practical
- **On-device key storage** — your Anthropic API key lives in `localStorage`
  and is sent only to Anthropic's API, never anywhere else

## C.F.O. extras

- **Business Snapshot** — enter cash on hand, monthly revenue/expenses, A/R,
  A/P, headcount, and free-form notes. The figures are injected into every
  request so the CFO does real math on real numbers, saved on-device.
- **Quick commands** — one-tap prompts for cash & runway, P&L read,
  collections, upcoming bills/filings, and weekly priorities.

## Setup

1. Open the app in Safari (iOS) or Chrome (desktop). On iPhone, use
   "Add to Home Screen" for a full-screen app experience.
2. Paste your Anthropic API key (`sk-ant-...`) and save. The key is shared
   between both apps — save it once.
3. For C.F.O., fill in the Business Snapshot so answers use your numbers.
4. Tap the orb and talk.

> **Note:** C.F.O. is a planning and analysis aid, not a licensed accountant.
> Confirm tax and legal matters with the brewery's accountant.
