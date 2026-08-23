# 03 — Exit-Readiness Checklist

**Source:** Chart of Accounts Review, July 26, 2026, from live QuickBooks
Online. **Lens:** every finding scored the way a private-equity buyer's
quality-of-earnings team would see it. Goal: books that survive diligence and
support the highest defensible multiple.

Statuses: `open → in_progress → fixed → verified`. A finding moves to `fixed`
only when the live number shows it, and `verified` only when John confirms the
underlying cause was addressed.

## The 10 findings (ordered by buyer concern)

| # | Area | Finding (baseline balances) | Fix | Status |
|---|---|---|---|---|
| 1 | Member equity is a thicket | Total equity −$12,929; ~24 member accounts, large negatives (John Rubbo Equity −$476,754); paired "Name"/"Name Equity" duplicates; misspellings ("Equiry", "Felecia", "Laura Tenebaum" under "David Tenebaum") | Reconcile to a clean cap table & operating agreement; consolidate pairs; fix names | open |
| 2 | Petty cash implausibly large | $42,702 — far beyond a till float; almost always uncleared cash or misclassification | Investigate entries; reclassify to a true small float | open |
| 3 | Accounts Payable negative | −$60,891 debit balance — prepayments/credits/misapplied payments | Reclassify prepayments to an asset; clean up | open |
| 4 | Related-party balances | Loan – John $62,053; Intercompany "Chicken Island"; large owner equity swings | Document terms; settle or formalize; feed the EBITDA add-back log | open |
| 5 | Catch-all revenue buckets | 4150 / 4140 / 4220 coexist; "Sales of Product Income" leaks $87; mirrors Toast-side mess | Retire catch-alls; enforce the Toast→GL taxonomy | open |
| 6 | No revenue-center dimension | GL can't tell bar/dining/patio/stage; 9101 has no matching cost grouping | Add QBO classes/locations; tag transactions | open |
| 7 | Tip & payroll clearing | Tips Payable $17,450 vs Payroll Clearing −$15,403 | Reconcile each pay cycle; enforce cash-tip capture upstream | open |
| 8 | Excise barely accrued | NY Excise Tax balance $0.01 despite active wholesale & internal beer movement | Stand up real TTB + NY excise accruals | open |
| 9 | Report integrity | P&L summary returned $0 net income while detail showed ~$123K | Fix account-type/mapping so summary foots to detail | open |
| 10 | Delivery & sign conventions | Aggregator receivables (GrubHub $12,762, UberEats, DoorDash) inside "Credit Card Cash Receivables"; 6210 Promos mis-nested negative | Separate & age aggregator receivables; re-nest contra accounts | open |

## The 5 structural moves

| ID | Move | Status |
|---|---|---|
| S1 | Revenue-center dimension (classes: bar, dining, patio, stage, brewery/wholesale) so every report slices the way diligence expects | open |
| S2 | Normalized-EBITDA schedule — capture add-backs as they occur (owner comp, related-party interest/rent, one-time costs) | open |
| S3 | Reconcile cap table; simplify equity to match the operating agreement | open |
| S4 | One menu taxonomy Toast→GL; kill catch-all sales accounts | open |
| S5 | Clean suspense items (petty cash, negative AP, payroll clearing) — no unexplained balances | open |

## What's already working (don't break it)

- Channels separated: Wholesale 4100s / Retail 4200s / Events 9101
- Revenue menu-categorized deeply enough for menu engineering
- COGS mirrors revenue (food / beer internal / beer external / wine-liquor; wholesale separate)
- Brewery-aware balance sheet: finished kegs, hops, WIP, keg-deposit liability, gift-card liability

## Caveats

Findings come from reading QuickBooks reports, not a transaction-level audit —
petty cash and negative AP need entry-level investigation to confirm cause.
Nothing here substitutes for the CPA's sign-off on final sale-ready statements.
