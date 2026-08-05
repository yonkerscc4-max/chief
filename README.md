# chief

Toast reporting for Yonkers Brewing — sales, transactions, and labor pulled
straight from the Toast API.

Python 3.11+, standard library only. Nothing to install.

## Getting credentials

Toast calls this **standard API access**, and you create the credentials
yourself in Toast Web — no partner application, no waiting on an integrations
review.

You need two things first:

- An active **Toast Restaurant Management Suite (RMS) Essentials** subscription
  or higher, for every location you want access to.
- The **8.4 Manage Integrations** permission on those locations.

Then:

1. In Toast Web, go to **Integrations > Toast API access > Manage credentials**.
2. **Create new credentials** → **Standard API**.
3. Name it something you will recognize later, e.g. `chief-reporting`.
4. Select these scopes:
   - `orders:read` — sales and transactions
   - `labor:read` and `labor.employees:read` — hours, tips, employee names
   - `restaurants:read` — location config and the business-day cutoff hour
   - `cashmgmt:read` — optional, for cash drawer and deposit reporting
5. Select your location(s) and confirm.

Toast then emails you the location GUIDs. Copy the client ID, client secret, and
API access URL from the credential page.

```bash
cp .env.example .env   # then fill it in
set -a && source .env && set +a
python -m toast check
```

`check` prints the restaurant name and business-day cutoff hour. If that works,
everything else will.

Standard API access is **production only** — Toast does not offer a sandbox for
it, so the first call hits live data. Every scope above is read-only.

### Keep the secret out of the repo

Toast's policy is explicit: a client secret committed to any repository, public
or private, counts as compromised and gets deactivated. `.env` is gitignored.
For anything scheduled, use your runner's secret store rather than a file on
disk. If a secret does leak, rotate it from the credential page — existing
tokens stay valid until they expire, so the rotation is not disruptive.

## Usage

```bash
# Yesterday, or any single business day. Toast applies your closeout hour,
# so a 2am Saturday sale lands on Friday where it belongs.
python -m toast sales --business-date 2026-08-04

# Rolling windows
python -m toast sales --days 7
python -m toast sales --start 2026-07-01 --end 2026-07-31

# One row per payment, for reconciliation
python -m toast transactions --business-date 2026-08-04 --format csv > aug04.csv

# Hours, tips, and estimated labor cost by employee
python -m toast labor --start 2026-07-21 --end 2026-08-03

# Anything else, for poking around
python -m toast raw /labor/v1/employees
```

Every command takes `--format json` for piping into something else.

## What each report contains

**sales** — orders, checks, guests, net sales, tax, tips, service charges
(gratuity broken out separately), discounts, refunds, total collected, and
average check. Broken down by payment type, dining option, and revenue center.
Voided and deleted orders, checks, and payments are excluded; voided checks are
counted separately so the number is visible rather than silently dropped.

**transactions** — one row per payment, with card type, last four, tip, refund
status, and the order/check GUIDs needed to tie a line back to Toast.

**labor** — per employee: shifts, regular and overtime hours, declared cash
tips, card tips, and estimated pay. Flags open shifts and missed breaks.

## On payroll

This reads Toast's **labor** API — the time clock. That covers hours, overtime,
tips, and a labor-cost estimate, which is what most payroll questions actually
turn on.

It is not Toast Payroll. The estimated-pay column is hours × wage, computed
here. It knows nothing about taxes, deductions, benefits, salaried staff, or a
wage that changed mid-period. Treat it as a management number, not a paystub.
For actual payroll runs, export from Toast Payroll directly.

## Development

```bash
python -m unittest discover -s tests
```

34 tests, no network access required — the client tests stub `urlopen` and the
report tests run against fixtures shaped like Toast's published response
samples.

Layout:

- `toast/client.py` — auth, token caching, retries, pagination
- `toast/reports.py` — pure aggregation functions over raw API payloads
- `toast/cli.py` — argument parsing and output formatting

## API reference

- [Authentication](https://doc.toasttab.com/doc/devguide/authentication.html)
- [Standard API access](https://doc.toasttab.com/doc/devguide/devApiAccessUserGuide.html)
- [Scopes](https://doc.toasttab.com/doc/devguide/devApiAccessScopes.html)
- [Orders API](https://doc.toasttab.com/openapi/orders/overview/)
- [Labor API](https://doc.toasttab.com/openapi/labor/overview/)
