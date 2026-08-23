# 02 — Toast → QuickBooks Category Map

**Version 1 — July 26, 2026.** One taxonomy tying every Toast sales item to the
right QuickBooks account, channel, and revenue center. Fixes the
uncategorized/duplicate items on the Toast side AND the catch-all accounts on
the QuickBooks side at the same time. Status: first pass built from the live GL
and the Per Guest Spend Brief — **validate against a Toast item-level export,
then lock.**

## Revenue map

| Toast category / item group | GL account (target) | Channel | Revenue center | Notes |
|---|---|---|---|---|
| Small Plates / Appetizers | 4211 Small Plates | Retail – Food | Dining Room | Largest food line; 38% of food revenue |
| Wings (Wing Night) | 4211 Small Plates (or new 4215 Wings) | Retail – Food | Dining Room | Currently UNCATEGORIZED in Toast — must map |
| Big Plates / Entrees | 4223 Big Plates | Retail – Food | Dining Room | |
| Sandwiches / Burgers | 4218 Sandwiches | Retail – Food | Dining Room | Burger decoy reprice lives here |
| Tacos | 4196 Tacos | Retail – Food | Dining Room | |
| Soups | 4197 Soups | Retail – Food | Dining Room | |
| Salads | 4198 Salads | Retail – Food | Dining Room | |
| Brunch | 4199 Brunch | Retail – Food | Dining Room | Sunday brunch package upside |
| Kids Meals | 4222 Kids Meals | Retail – Food | Dining Room | |
| Desserts | 4224 Desserts | Retail – Food | Dining Room | Under-sold; move onto food menu |
| Catering | 4250 Retail Catering | Retail – Food | Off-Premise | |
| Beer – House / Draft / Flights | 4212 Beer | Retail – Beverage | Bar | House beers listed first |
| Beer – External (Corona, Coors…) | 4212 Beer | Retail – Beverage | Bar | Same revenue acct; DIFFERENT COGS (5220) |
| Beer – Six-packs / cans to go | New 4215 Beer To-Go (recommend) | Retail – Beverage | Bar | $7.2K/quarter and working |
| Liquor / Cocktails | 4213 Liquor | Retail – Beverage | Bar | The $4,222 uncategorized Margarita belongs here |
| Wine | 4214 Wine | Retail – Beverage | Bar | |
| Non-Alcoholic Beverages | 4221 Non Alcoholic Beverages | Retail – Beverage | Bar | NA beer / mocktail opportunity |
| Merchandise | 4219 Merchandise | Retail – Other | Bar | Needs a matching COGS account |
| Live Music / Cover / Events | 9101 Live Music and Event Sales | Venue – Events | Stage / Venue | Pair with 7245/7246 event costs |
| Wholesale – Packaged 4/6/12 | 4110 Packaged Beer - 4/6/12 | Wholesale | Wholesale | |
| Wholesale – Keg 1/6 bbl | 4120 Kegged Beer - 1/6 bbl | Wholesale | Wholesale | |
| Wholesale – Keg 1/2 bbl | 4130 Kegged Beer - 1/2 bbl | Wholesale | Wholesale | |

## COGS map (targets to confirm against recipes)

| Category | COGS account (target) | Target COGS % | Notes |
|---|---|---|---|
| All food categories | 5210 Food Cogs | ~30% (28–32) | |
| Beer – house/draft | 5215 Beer Cogs - Internal | ~20% (18–22) | Transfer cost |
| Beer – external | 5220 Beer Cogs - External | ~32% | Bought 25–30 pts worse margin — watch mix |
| Liquor / cocktails | 5230 Wine/Liquor Cogs | ~20% (18–22) | |
| Wine | 5230 (consider new 5231 Wine Cogs) | ~33% | Wine runs higher |
| Non-alcoholic | 5240 Supplies (or new NA Cogs) | ~18% | No clean COGS today |
| Merchandise | New 5250 Merch Cogs (recommend) | ~50% | No COGS account exists today |
| Paper / supplies | 5240 Supplies | — | Non-product retail supplies |
| Wholesale beer | 5100 Wholesale Cogs | — | Keep separate from retail |

## Accounts to fix

| Account / item | Problem | Action |
|---|---|---|
| 4150 Sales | Vague catch-all | Retire; reclassify to real categories |
| 4140 Other Sales (wholesale) | Catch-all | Retire or define narrowly; move to 4110–4130 |
| 4220 Other Sales (retail) | Catch-all | Retire; map items to real categories |
| 4225 Promos / 6210 Promos | Promo shown as sales; 6210 mis-nested under Gross Retail, negative | Move to contra-revenue/discount account |
| Sales of Product Income | QBO default leaking $86.67 | Close into correct category; stop using |
| Uncategorized Toast items | e.g. $4,222 Margarita | Map every item per the revenue map |
| Duplicate beer buttons | Same beer split across buttons | Merge to one item → 4212 Beer |
| Petty Cash ($42,702) | Implausibly large for a till float | Investigate entries; reclassify |
| Accounts Payable (−$60,891) | Negative/debit AP | Reclassify prepayments to an asset |

## Revenue centers (proposed QuickBooks classes)

| Class | What routes here | Why |
|---|---|---|
| Bar | All beverage; bar-area food | The engine — 54% of sales are alcohol |
| Dining Room | Table food service | Restaurant-day economics (Tue–Thu, Sun) |
| Patio | Seasonal outdoor | Separates weather-driven capacity |
| Stage / Venue | Live music, cover, events (9101) | The Fri/Sat "second company" |
| Online / QR | QR-at-table and online orders (~16% of sales) | The unnamed channel |
| Off-Premise | Delivery apps & takeout | Aggregator fees & receivables live here |
| Wholesale | Distributor sales | Three-tier channel, distinct margins |
| Brewery / Production | Production inputs, kegs, WIP | Brewery costing & TTB/excise base |
