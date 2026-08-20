#!/usr/bin/env python3
"""
Toast API client for Yonkers Brewing Co.

Reconstructed to match the interface setup_toast.sh expects. Standard API
access is read-only. Standard library only, so there is nothing to pip
install before setup_toast.sh runs its verification step.

Credentials are read from ~/.config/toast/credentials.env (written by
setup_toast.sh). Real environment variables win over the file, so CI can
inject them without touching disk.

    from toast_client import Toast
    t = Toast()
    orders = t.orders_for_business_date("20260801")

Run it directly to verify a connection:

    python3 toast_client.py
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path

CRED_FILE = Path.home() / ".config" / "toast" / "credentials.env"
DEFAULT_HOSTNAME = "https://ws-api.toasttab.com"

# Toast caps pageSize at 100 on /ordersBulk.
MAX_PAGE_SIZE = 100

# Toast asks for spacing between wide-range calls. Day-at-a-time requests are
# much smaller than that, so a short pause is enough to stay well inside the
# per-restaurant rate limit.
DEFAULT_REQUEST_DELAY = 0.25


class ToastError(RuntimeError):
    """Any failure talking to Toast: config, auth, or HTTP."""


def _load_credentials() -> dict[str, str]:
    """Merge credentials.env with the real environment. Environment wins."""
    values: dict[str, str] = {}

    if CRED_FILE.exists():
        for raw in CRED_FILE.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            values[key.strip()] = value.strip().strip("'\"")

    for key in (
        "TOAST_API_HOSTNAME",
        "TOAST_CLIENT_ID",
        "TOAST_CLIENT_SECRET",
        "TOAST_USER_ACCESS_TYPE",
        "TOAST_RESTAURANT_GUID",
        "TOAST_MANAGEMENT_GROUP_GUID",
    ):
        if os.environ.get(key):
            values[key] = os.environ[key]

    missing = [
        key
        for key in ("TOAST_CLIENT_ID", "TOAST_CLIENT_SECRET", "TOAST_RESTAURANT_GUID")
        if not values.get(key)
    ]
    if missing:
        raise ToastError(
            "Missing credentials: {}.\n"
            "Run 'bash setup_toast.sh' to write {}, or export them.".format(
                ", ".join(missing), CRED_FILE
            )
        )

    values.setdefault("TOAST_API_HOSTNAME", DEFAULT_HOSTNAME)
    values.setdefault("TOAST_USER_ACCESS_TYPE", "TOAST_MACHINE_CLIENT")
    return values


def _business_date_str(value) -> str:
    """Normalize a business date to the YYYYMMDD string Toast wants."""
    if isinstance(value, (date, datetime)):
        return value.strftime("%Y%m%d")

    text = str(value).strip().replace("-", "")
    if len(text) != 8 or not text.isdigit():
        raise ValueError(f"business date must be YYYYMMDD, got {value!r}")
    # Reject things like 20260230 before spending a request on them.
    datetime.strptime(text, "%Y%m%d")
    return text


def _to_date(value) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.strptime(_business_date_str(value), "%Y%m%d").date()


class Toast:
    """Read-only client for the Toast Standard API."""

    def __init__(self, *, request_delay: float = DEFAULT_REQUEST_DELAY) -> None:
        creds = _load_credentials()
        self.hostname = creds["TOAST_API_HOSTNAME"].rstrip("/")
        self.client_id = creds["TOAST_CLIENT_ID"]
        self._client_secret = creds["TOAST_CLIENT_SECRET"]
        self.user_access_type = creds["TOAST_USER_ACCESS_TYPE"]
        self.restaurant_guid = creds["TOAST_RESTAURANT_GUID"]
        self.management_group_guid = creds.get("TOAST_MANAGEMENT_GROUP_GUID", "")
        self.request_delay = request_delay

        self._token: str | None = None
        self._token_expires_at = 0.0

    # ---------------------------------------------------------------- auth

    def _authenticate(self) -> str:
        body = json.dumps(
            {
                "clientId": self.client_id,
                "clientSecret": self._client_secret,
                "userAccessType": self.user_access_type,
            }
        ).encode()

        request = urllib.request.Request(
            f"{self.hostname}/authentication/v1/authentication/login",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read())
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")[:500]
            if exc.code in (401, 403):
                raise ToastError(
                    "Toast rejected the credentials (HTTP {}). Check the client ID "
                    "and secret, and confirm the credential set is active in "
                    "Toast Web.\n{}".format(exc.code, detail)
                ) from exc
            raise ToastError(f"Authentication failed (HTTP {exc.code}): {detail}") from exc
        except urllib.error.URLError as exc:
            raise ToastError(f"Could not reach {self.hostname}: {exc.reason}") from exc

        token = payload.get("token") or {}
        access_token = token.get("accessToken")
        if not access_token:
            raise ToastError(f"No accessToken in the auth response: {payload!r}")

        # expiresIn is milliseconds. Renew a minute early so a long paginated
        # pull cannot expire mid-loop.
        expires_in_ms = token.get("expiresIn") or 0
        lifetime = (expires_in_ms / 1000.0) if expires_in_ms else 300.0
        self._token_expires_at = time.time() + max(lifetime - 60, 30)
        self._token = access_token
        return access_token

    def _access_token(self) -> str:
        if self._token is None or time.time() >= self._token_expires_at:
            return self._authenticate()
        return self._token

    # ------------------------------------------------------------- request

    def _get(self, path: str, params: dict | None = None, *, _retry_auth: bool = True):
        url = f"{self.hostname}{path}"
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"

        request = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {self._access_token()}",
                "Toast-Restaurant-External-ID": self.restaurant_guid,
                "Accept": "application/json",
            },
        )

        last_error: Exception | None = None
        for attempt in range(5):
            try:
                with urllib.request.urlopen(request, timeout=60) as response:
                    raw = response.read()
                    return json.loads(raw) if raw else None
            except urllib.error.HTTPError as exc:
                # An expired token mid-pull: re-auth once and replay.
                if exc.code == 401 and _retry_auth:
                    self._token = None
                    return self._get(path, params, _retry_auth=False)

                if exc.code == 429 or exc.code >= 500:
                    retry_after = exc.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else 2.0 * (2**attempt)
                    last_error = exc
                    time.sleep(min(delay, 60))
                    continue

                detail = exc.read().decode(errors="replace")[:500]
                if exc.code == 403:
                    raise ToastError(
                        "HTTP 403 on {}. The credential set is probably missing a "
                        "scope for this endpoint.\n{}".format(path, detail)
                    ) from exc
                raise ToastError(f"HTTP {exc.code} on {path}: {detail}") from exc
            except urllib.error.URLError as exc:
                last_error = exc
                time.sleep(2.0 * (2**attempt))

        raise ToastError(f"Gave up on {path} after 5 attempts: {last_error}")

    # ------------------------------------------------------------ endpoints

    def restaurant(self) -> dict:
        """The configured restaurant. Needs the restaurants:read scope."""
        return self._get(f"/restaurants/v1/restaurants/{self.restaurant_guid}")

    def restaurant_name(self) -> str:
        info = self.restaurant() or {}
        general = info.get("general") or {}
        return general.get("name") or info.get("name") or "(unnamed)"

    def menus(self) -> dict:
        """Published menus. Needs the menus:read scope."""
        return self._get("/menus/v2/menus")

    def orders_for_business_date(self, business_date, *, page_size: int = MAX_PAGE_SIZE) -> list:
        """
        Every order on one business day, following pagination to the end.

        businessDate, not calendar date: Toast assigns orders to a business day
        using the restaurant's closeoutHour, so a show that ends at 1am lands on
        the night it started. This is also what Toast Web reports on, so numbers
        here reconcile against the dashboard.
        """
        params_date = _business_date_str(business_date)
        page_size = max(1, min(page_size, MAX_PAGE_SIZE))

        orders: list = []
        page = 1
        while True:
            batch = self._get(
                "/orders/v2/ordersBulk",
                {"businessDate": params_date, "page": page, "pageSize": page_size},
            )
            if not batch:
                break

            orders.extend(batch)
            if len(batch) < page_size:
                break

            page += 1
            if self.request_delay:
                time.sleep(self.request_delay)

            if page > 1000:  # ~100k orders in a day: something is wrong.
                raise ToastError(
                    f"Pagination did not terminate for businessDate {params_date}."
                )

        return orders

    def orders_for_range(self, start, end, *, progress=None) -> list:
        """
        Every order across an inclusive range of business dates.

        One request per business day, deduped by order GUID. This is
        deliberately not a single wide startDate/endDate call: a 90-day window
        came back with 7,000 orders and looked complete, while the same range
        pulled in small chunks came back with 15,028 and reconciled against net
        sales to within 0.02%. A wide window under-returns silently, so this
        never opens one.

        progress, if given, is called with (business_date, running_total).
        """
        first, last = _to_date(start), _to_date(end)
        if first > last:
            raise ValueError(f"start {first} is after end {last}")

        seen: set[str] = set()
        orders: list = []
        cursor = first

        while cursor <= last:
            for order in self.orders_for_business_date(cursor):
                guid = order.get("guid")
                # Keep GUID-less orders rather than collapsing them together.
                if guid is not None:
                    if guid in seen:
                        continue
                    seen.add(guid)
                orders.append(order)

            if progress:
                progress(cursor.strftime("%Y%m%d"), len(orders))

            cursor += timedelta(days=1)
            if self.request_delay and cursor <= last:
                time.sleep(self.request_delay)

        return orders


# --------------------------------------------------------------- money

def net_sales(orders) -> float:
    """
    Net sales across orders, skipping voided and deleted orders and checks.

    check["amount"] is net sales. check["totalAmount"] includes tax and tips
    and runs 15-17% higher, so using it as revenue overstates weekly sales by
    roughly 25%. This function reads "amount" for that reason. Do not "fix" it.
    """
    total = 0.0
    for order in orders:
        if order.get("voided") or order.get("deleted"):
            continue
        for check in order.get("checks") or []:
            if check.get("voided") or check.get("deleted"):
                continue
            total += float(check.get("amount") or 0.0)
    return round(total, 2)


def _verify() -> int:
    try:
        client = Toast()
    except ToastError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1

    print(f"Host       : {client.hostname}")
    print(f"Client ID  : {client.client_id}")
    print(f"Restaurant : {client.restaurant_guid}")
    print()

    try:
        name = client.restaurant_name()
    except ToastError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1

    print(f"Connected to: {name}")
    print()

    # A sample order from the most recent business day that has any. Quiet
    # nights and closed days are normal, so look back a little before giving up.
    today = date.today()
    for days_back in range(0, 8):
        business_date = today - timedelta(days=days_back)
        try:
            orders = client.orders_for_business_date(business_date)
        except ToastError as exc:
            print(f"Could not read orders: {exc}", file=sys.stderr)
            return 1

        if orders:
            stamp = business_date.strftime("%Y%m%d")
            print(f"Business date {stamp}: {len(orders)} orders, "
                  f"net sales ${net_sales(orders):,.2f}")
            print()
            print("Sample order:")
            print(json.dumps(orders[0], indent=2)[:2000])
            return 0

    print("Authentication and restaurants:read both work, but no orders were "
          "found in the last 8 business days.")
    return 0


if __name__ == "__main__":
    sys.exit(_verify())
