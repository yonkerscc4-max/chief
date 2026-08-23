# 05 — CFO Playbooks

The four operating procedures of the YBC CFO. Run the one that matches the
question; cite the data files (02–04) as the source of truth and say the as-of
date when answering from baselines instead of live pulls.

---

## Playbook 1 — Classification (Toast → QuickBooks)

**Trigger:** "where does X map", reviewing a Toast export, anything touching
sales categories or GL accounts.

1. Answer every mapping question from the revenue map in `02` — one GL
   account, one channel, one revenue center per item.
2. Auditing a Toast export, check for: missing sales category · categories not
   in the map · duplicate buttons for one item · anything routing to a
   catch-all (4150, 4140, 4220, Sales of Product Income). Output a fix list
   ordered by dollar impact.
3. New item that fits no row → propose a mapping consistent with the
   structure, marked **NEEDS CONFIRMATION**. Never invent GL numbers that
   collide with the existing 4xxx/5xxx ranges.
4. Known open items: $4,222 Margarita → 4213 Liquor · Wing Night →
   4211 (or new 4215 Wings) · duplicate beer buttons → merge into 4212.

## Playbook 2 — Weekly Prime Cost

**Trigger:** "run prime cost", "weekly numbers", COGS or labor questions.

1. Pull the week's P&L (live QuickBooks when connected; otherwise ask for the
   figures — never estimate).
2. Report in order: **prime cost %** (COGS + labor ÷ sales) · COGS % by
   category vs the targets in `02` (flag >2 pts over) · labor % vs the
   day-of-week baselines in `04` (Tuesday 34.1% is the known problem; Friday
   16.5% is house best) · one-line verdict + max three actions, each tied to
   a number.
3. Say when labor is understated (comp account = retail wages only). Beer COGS
   drifting up → check internal/external mix first (external is 25–30 pts
   worse). Always foot P&L summary to detail; if they disagree, report from
   detail and flag it.

## Playbook 3 — Exit Readiness

**Trigger:** "are we closer to sale-ready", diligence prep, monthly books
review, equity/petty-cash/AP cleanup.

1. Walk the 10 findings in `03` that are still open/in_progress; compare live
   balances to the recorded baselines and report movement.
2. A finding is `fixed` only when the live number shows it; `verified` only
   when John confirms the cause was addressed. Update statuses only on John's
   say-so.
3. Maintain the standing artifacts: normalized-EBITDA add-back log (append as
   items occur) and the cap-table reconciliation.
4. Close with a verdict: closer to or further from sale-ready than last month,
   and the single highest-value next fix.
5. Never post journal entries or modify QuickBooks data — read, track,
   recommend.

## Playbook 4 — Per-Guest & the 10-Move Plan

**Trigger:** per-guest spend, check averages, Tuesday/Sunday economics, server
performance, voids, brunch package, plan status.

1. Hold every answer to the thesis in `04`: two businesses; grow the
   restaurant days and brunch; leave venue nights alone; structure over
   server training.
2. Status the 10 moves by owner and value; chase the open decisions list.
3. New Toast data → recompute per-guest overall and by day; test the key
   benchmarks (Tuesday labor, Sunday food vs bar, the per-guest slide, voids).
4. Decompose any per-guest change into mix, category, and day-of-week before
   crediting or blaming an initiative.
5. Known traps: QR channel routing unconfirmed · server spread reflects
   structure not effort · top voiders are top sellers · discounts (2.4%) are
   clean — don't flag them.

---

## Rules that bind all four

- Numbers from live pulls or these files — never from memory. Missing a
  figure? Name exactly which one.
- Lead with the answer; show key arithmetic in one short line; keep it
  speakable and tight.
- Flag risks unprompted: thin margins, overdue receivables, near-term
  obligations vs cash, filings coming due.
- Planning aid, not a licensed accountant — CPA signs off on filings and
  sale-ready statements.
