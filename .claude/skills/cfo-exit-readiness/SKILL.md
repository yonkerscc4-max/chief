---
name: cfo-exit-readiness
description: Track and re-check the Yonkers Brewing exit-readiness findings so the books drift toward sale-ready. Use when John asks about exit readiness, diligence prep, book cleanup status, the monthly books review, equity/petty-cash/AP cleanup, or anything about preparing the company for sale. Skill #19 of the YBC CFO agent.
---

# CFO Skill #19 — Exit Readiness

The live checklist is `cfo/data/exit_readiness_checklist.json`: 10 findings and
5 structural moves from the July 26, 2026 Chart of Accounts Review, each with a
`status` (`open` → `in_progress` → `fixed` → `verified`). This skill keeps that
checklist honest against live QuickBooks data.

## The lens

Score everything the way a PE buyer's quality-of-earnings team would. Messy
equity reads as weak controls. Unexplained cash is a red flag. Related-party
balances get scrutinized. The goal is books that survive diligence and support
the highest defensible multiple.

## Monthly re-check procedure

1. Load the checklist JSON.
2. Pull live data via the QuickBooks connector (ToolSearch:
   `qbo_accounting_get_balance_sheet`,
   `profit_loss_quickbooks_account`, `qbo_accounting_get_ap_aging_summary`).
3. For each finding still `open`/`in_progress`, re-read the relevant balance
   and report movement vs the recorded baseline:
   - #1 equity: total equity and count of member accounts (baseline −$12,929, ~24 accounts)
   - #2 petty cash: balance (baseline $42,702)
   - #3 AP: sign and balance (baseline −$60,891)
   - #4 related-party: Loan – John (baseline $62,053), Chicken Island intercompany
   - #5 catch-alls: any period activity in 4150/4140/4220/Sales of Product Income
   - #7 tips/payroll clearing: Tips Payable (baseline $17,450) vs Payroll Clearing (baseline −$15,403)
   - #8 excise: NY excise accrual balance (baseline $0.01)
   - #9 report integrity: does the P&L summary foot to its detail this month?
   - #10 aggregator receivables: still inside Credit Card Cash Receivables?
4. A finding only moves to `fixed` when the live number shows it, and to
   `verified` only when John confirms the underlying cause was addressed (not
   just the balance moved). Update the JSON statuses in the repo when John
   agrees, and commit.
5. Close with a one-paragraph verdict: closer to or further from sale-ready
   than last month, and the single highest-value next fix.

## Standing artifacts to maintain

- **Normalized-EBITDA add-back log** (structural move S2): owner compensation,
  related-party interest/rent, one-time costs — append as they occur, don't
  reconstruct under deadline. Keep in `cfo/data/ebitda_addbacks.json` once the
  first entry exists.
- **Cap-table reconciliation** (S3): equity section must match the operating
  agreement.

## Boundaries

Findings come from reading QuickBooks reports, not a transaction-level audit.
Petty cash and negative AP need entry-level investigation to confirm cause.
Nothing here substitutes for the CPA's sign-off on final sale-ready statements
— say so when reporting. Never post journal entries or modify QBO data; this
skill reads, tracks, and recommends.
