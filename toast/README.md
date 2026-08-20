# Toast API access

Read-only Standard API access to Yonkers Brewing Co. orders, payments, checks,
menus, labor and inventory.

## Status

Not connected yet. Creating the credential set has to be done by a human
signed into Toast Web — see below. Everything downstream of that is ready.

## 1. Create the credentials (Toast Web, human required)

Toast Web > Integrations > Toast API access > Manage credentials >
**Create new credentials** > down arrow > **Standard API**.

Name it something recognizable, then select scopes. The scripts here need at
minimum:

| Scope              | Why |
| ------------------ | --- |
| `orders:read`      | the orders API, where almost everything lives |
| `restaurants:read` | required, or the verification step fails |
| `menus:read`       | menus |
| `config:read`      | configuration |

`labor:read`, `cashmgmt:read` and `stock:read` are optional. Skip
`guest.pi:read` and `delivery_info.address:read` unless guest personal
information is actually needed in the order data.

Select **Yonkers Brewing Co.** as the location, then create.

**Copy the client secret immediately — Toast displays it exactly once.**
Everything else stays on the credentials page, and *View credentials in JSON
format* gives the client ID, restaurant GUID and group GUID in one block.

## 2. Run the setup

Put `setup_toast.sh` and `toast_client.py` in the same folder and run:

```
bash setup_toast.sh
```

It prompts for the four values, writes `~/.config/toast/credentials.env` with
`600` permissions, and verifies by printing the restaurant name plus a sample
order. The restaurant name means it worked.

`toast_client.py` also reads `TOAST_*` environment variables, which take
precedence over the file — that is the path for CI, where writing a secret to
disk is not wanted.

The credentials file is not in this repository and must never be committed.

## 3. Usage

```python
from toast_client import Toast, net_sales

t = Toast()
orders = t.orders_for_business_date("20260801")
print(net_sales(orders))

# Inclusive range of business dates, one request per day, deduped by GUID.
week = t.orders_for_range("20260801", "20260807")
```

Standard API access is read-only; there is no write path. Email marketing and
the forward-looking reservation book are not exposed by the API at all and
stay in the dashboard.

## 4. Things that will burn you

**Net vs. total.** `check["amount"]` is net sales. `check["totalAmount"]`
includes tax and tips and runs 15-17% higher — using it as revenue overstates
weekly sales by about 25%. `net_sales()` reads `amount` for that reason and
skips voided and deleted orders and checks.

**Wide date windows under-return silently.** A single 90-day `ordersBulk`
request stopped at 7,000 orders and looked like a clean complete result; the
same range in small chunks returned 15,028, which reconciled against net sales
to within 0.02%. `orders_for_range()` therefore never opens a wide window — it
issues one request per business date and dedupes by order GUID. Toast's own
guidance caps `startDate`/`endDate` at about a month and asks for 5-10 seconds
between wide calls.

**Business date, not calendar date.** Toast assigns an order to a business day
using the restaurant's configured `closeoutHour`, so a show ending at 1am
lands on the night it started. `businessDate` is also what Toast Web reports
on, so numbers pulled this way reconcile against the dashboard. Note that
`startDate`/`endDate` filter on order *modification* time, which is a
different question and rarely the one being asked.

**Roughly 45% of revenue is uncategorized**, including the entire food menu
and door tickets, so category reports read $0 for FOOD and EVENTS. That is a
menu configuration issue on our end, not an API one, and there is a rebuild
list for it.

## 5. Separate credential sets

Toast logs calls per credential set, so separate keys keep integrations
attributable. AJ's set carries the nightly ticket count that goes to artist
management and `close_show.py`, which is how bands get settled at the end of
the night; a shared key that got rotated would take all of that down at once.
A management group holds up to 100 credential sets, so there is no reason to
share one.
