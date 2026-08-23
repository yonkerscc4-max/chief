---
name: cfo-prime-cost
description: Run the Yonkers Brewing weekly prime-cost report (COGS + labor as % of sales) from live QuickBooks data. Use when John asks for prime cost, weekly numbers, COGS review, labor percentage, or a weekly financial check-in. Skill #7 of the YBC CFO agent.
---

# CFO Skill #7 — Weekly Prime Cost

Prime cost = product (COGS) + labor, as a percent of sales. It is the single
number that tells a restaurant/venue operator whether the week worked.

## Data sources

Pull live via the Intuit QuickBooks connector (load via ToolSearch:
`mcp__Intuit_QuickBooks__profit_loss_quickbooks_account` for the P&L over the
report window; `qbo_accounting_get_sales_by_product_summary` for mix;
`qbo_payroll_get_company_last_payroll_run` / payslips for labor detail when the
P&L compensation lines are insufficient). If the connector is unavailable, say
so and ask for the figures rather than estimating.

## Report structure

Compute for the week (and 4-week trailing for trend):

| Line | Source accounts |
|---|---|
| Retail sales (net) | 4200s retail income group |
| Wholesale sales | 4110/4120/4130 |
| Events / live music | 9101 |
| Food COGS | 5210 |
| Beer COGS — internal | 5215 |
| Beer COGS — external | 5220 |
| Wine/Liquor COGS | 5230 |
| Wholesale COGS | 5100 |
| Labor | retail compensation + any other comp accounts found — name which |

Then report, in this order:
1. **Prime cost %** (total COGS + labor) / total sales — the headline.
2. COGS % by category vs the targets in `cfo/data/toast_qbo_map.json` →
   `cogs_map.target_cogs_pct`. Flag any category >2 pts over target.
3. Labor % vs the day-of-week baselines in `cfo/data/revenue_plan.json` →
   `day_profile_last_90d.labor_pct` (Tuesday's 34.1% is the known problem;
   Friday's 16.5% is the house best).
4. One-line verdict and at most three actions, each tied to a number.

## Known context

- Back-of-envelope prime cost runs low-to-mid 50s % — workable, but the GL's
  compensation account captures **retail wages only**, so true all-in labor may
  read higher. Say when your labor number is understated for this reason.
- External beer (5220) is bought at 25–30 pts worse margin than house beer —
  when beer COGS % drifts up, check the internal/external mix first.
- The P&L summary fields have returned $0 while detail showed real numbers
  (exit-readiness finding #9). Always foot the summary to the detail; if they
  disagree, report from the detail and flag it.

Keep the report tight — it should read in under a minute. Numbers first,
narrative second.
