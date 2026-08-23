---
name: cfo-per-guest
description: Track Yonkers Brewing per-guest spend and the 10-move revenue plan. Use when John asks about per-guest spend, check averages, the spend decline, Tuesday/Sunday economics, server performance, voids, the brunch package, menu moves, or the status of the revenue plan. Companion analytics skill of the YBC CFO agent.
---

# CFO Skill — Per-Guest Spend & the 10-Move Plan

The reference data is `cfo/data/revenue_plan.json`: the monthly per-guest trend,
the day-of-week economics table, the 10 ranked moves with owners and value
estimates, watch items, and the still-coming data list. Source: Per Guest Spend
Brief v2 (Toast data through July 22, 2026).

## The thesis (hold every answer to it)

Volume is winning, spend is slipping: per-guest fell $30.34 → $23.56 over six
months while sales nearly doubled. YBC is **two businesses** — a restaurant
Tue–Thu & Sun, a music venue Fri–Sat nights. The plan grows the restaurant days
and brunch, and leaves the venue nights alone. Every move is structural (menus,
bundles, prompts, staffing) — nothing depends on server training surviving
turnover.

## Jobs

1. **Status the plan.** Report the 10 moves by status, owner, and value. Chase
   the decisions the brief left on the table (brunch price, Tuesday staffing
   call, menu reprint date, void codes on, QR routing confirmed, server
   debrief, merch case location).

2. **Refresh the numbers.** When new Toast data arrives (export or figures from
   John), recompute per-guest overall and by day, compare to
   `monthly_trend` / `day_profile_last_90d`, and update the JSON (commit when
   John agrees). Key benchmarks to re-test:
   - Tuesday labor 34.1% of sales vs Wednesday 19.3% — did restructure land?
   - Sunday food $10.96/guest with bar only $11.06 — is brunch package lifting it?
   - Per-guest trend — has the six-month slide stopped?
   - Voids ~$12.6K/quarter — falling once reason codes are on?

3. **Decompose a change.** When per-guest moves, split it: mix (seasonal,
   venue vs restaurant nights), category (alcohol $13.35 / food $9.50 / NA
   $0.32 / dessert $0.12 baselines), and day-of-week, before crediting or
   blaming any initiative.

4. **Guard against bad reads.** Known traps from the brief: the Online/QR
   channel (~16% of sales) is unconfirmed in routing; server per-guest spread
   ($22.01–$29.94) tracks structure not effort; top voiders are top sellers
   (volume, not misconduct); discounts at 2.4% are clean — don't flag them.

## Cross-links

Menu taxonomy questions → `cfo-classification`. Weekly cost side → 
`cfo-prime-cost`. Revenue-center buildout (needed to decompose spend by room)
is exit-readiness structural move S1 → `cfo-exit-readiness`.
