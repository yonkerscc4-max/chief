# YBC CFO Agent

The AI CFO for **Yonkers Brewing Company LLC** — an agent build, separate from
C.H.I.E.F. (which handles John's personal life and lives in `index.html`).

The CFO works from **live data** — QuickBooks Online via the Intuit connector,
and Toast POS exports — not manual entry. This directory holds its knowledge
base; the skills in `.claude/skills/cfo-*` hold its operating procedures. Open
this repo in a Claude session with the QuickBooks connector attached and the
skills trigger on plain-English asks ("run prime cost", "where does the
Margarita map", "are we closer to sale-ready").

## Skills

| # | Skill | Job |
|---|-------|-----|
| 1 | `cfo-classification` | Enforce the Toast→QuickBooks taxonomy; audit Toast exports for uncategorized/duplicate items; guard the catch-all accounts |
| 7 | `cfo-prime-cost` | Weekly prime cost (COGS + labor % of sales) from live QBO, by category vs targets |
| 19 | `cfo-exit-readiness` | Monthly re-check of the 10 diligence findings + 5 structural moves so the books drift toward sale-ready |
| — | `cfo-per-guest` | Per-guest spend trend, day-of-week economics, and the 10-move revenue plan tracker |

Skill numbers follow the roster from the original CFO build. The other numbered
skills from that roster can be scaffolded here the same way as they come up.

## Data (the agent's working memory)

| File | Contents |
|------|----------|
| `data/toast_qbo_map.json` | Toast→GL revenue map, COGS map with target %, accounts to fix, revenue centers. v1 — validate against a Toast item export, then lock. |
| `data/exit_readiness_checklist.json` | The 10 findings + 5 structural moves with live statuses, and the YTD baseline numbers they were scored against. |
| `data/revenue_plan.json` | Per-guest trend, day profile, the 10 moves with owners/values/statuses, watch items. |

Statuses in these files are updated by the agent **only when John confirms**,
and committed so the history is auditable.

## Source documents

`docs/` holds the founding documents, kept verbatim:

- `Yonkers_Chart_of_Accounts_Review.docx` — exit-readiness findings from live QBO (Jul 26, 2026)
- `YBC_Per_Guest_Spend_Brief_v2.docx` — leadership brief, Toast data through Jul 22, 2026
- `Yonkers_Toast_to_QuickBooks_Category_Map.xlsx` — taxonomy v1 (also encoded in `data/toast_qbo_map.json`)

## Ground rules

- QuickBooks access is **read-only by default** — the agent never creates or
  modifies QBO accounts, products, invoices, or transactions without John's
  explicit go-ahead in the conversation.
- Numbers come from live pulls or the data files, never from memory. If a
  figure isn't available, the agent names exactly what it needs.
- Planning and analysis aid, not a licensed accountant — CPA signs off on
  anything filed or sale-ready.
