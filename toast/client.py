"""Minimal Toast Web API client.

Standard library only -- no install step, which matters because this tends to
get run from a laptop or a cron box rather than a managed deploy.

Docs: https://doc.toasttab.com/doc/devguide/authentication.html
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

# Toast expires tokens on the order of hours, but renew early so a long report
# pull can't have a token die out from under it mid-pagination.
_TOKEN_REFRESH_MARGIN_SECONDS = 300

_RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})
_MAX_ATTEMPTS = 5


class ToastError(RuntimeError):
    """An API call failed in a way that retrying will not fix."""

    def __init__(self, message: str, *, status: int | None = None, body: str = ""):
        super().__init__(message)
        self.status = status
        self.body = body


class ToastAuthError(ToastError):
    """Credentials were rejected."""


def iso8601(moment: datetime) -> str:
    """Format a datetime the way Toast's date filters expect.

    Toast wants a millisecond fraction and a numeric UTC offset, e.g.
    ``2016-01-01T14:13:12.000+0400``. Naive datetimes are read as UTC.
    """
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.strftime("%Y-%m-%dT%H:%M:%S.") + f"{moment.microsecond // 1000:03d}" + moment.strftime("%z")


class ToastClient:
    """Authenticated caller for the Toast REST APIs.

    Credentials come from Toast Web under Integrations > Toast API access.
    Pass them in, or leave them out to read from the environment:
    ``TOAST_HOSTNAME``, ``TOAST_CLIENT_ID``, ``TOAST_CLIENT_SECRET``,
    ``TOAST_RESTAURANT_GUID``.
    """

    def __init__(
        self,
        hostname: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        restaurant_guid: str | None = None,
        *,
        timeout: int = 60,
    ):
        self.hostname = (hostname or os.environ.get("TOAST_HOSTNAME", "")).strip()
        self.client_id = client_id or os.environ.get("TOAST_CLIENT_ID", "")
        self.client_secret = client_secret or os.environ.get("TOAST_CLIENT_SECRET", "")
        self.restaurant_guid = restaurant_guid or os.environ.get("TOAST_RESTAURANT_GUID", "")
        self.timeout = timeout

        missing = [
            name
            for name, value in (
                ("TOAST_HOSTNAME", self.hostname),
                ("TOAST_CLIENT_ID", self.client_id),
                ("TOAST_CLIENT_SECRET", self.client_secret),
                ("TOAST_RESTAURANT_GUID", self.restaurant_guid),
            )
            if not value
        ]
        if missing:
            raise ToastError(f"Missing Toast configuration: {', '.join(missing)}. See .env.example.")

        # Toast Web hands you the API access URL with a scheme; tolerate either form.
        self.hostname = self.hostname.replace("https://", "").replace("http://", "").rstrip("/")

        self._token: str | None = None
        self._token_expires_at: float = 0.0

    # -- auth ------------------------------------------------------------

    def _authenticate(self) -> None:
        payload = json.dumps(
            {
                "clientId": self.client_id,
                "clientSecret": self.client_secret,
                "userAccessType": "TOAST_MACHINE_CLIENT",
            }
        ).encode()

        request = urllib.request.Request(
            f"https://{self.hostname}/authentication/v1/authentication/login",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = json.loads(response.read())
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")
            if exc.code in (400, 401, 403):
                raise ToastAuthError(
                    "Toast rejected the client credentials. Confirm the client ID and "
                    "secret, and that the secret has not been rotated in Toast Web.",
                    status=exc.code,
                    body=detail,
                ) from exc
            raise ToastError(f"Authentication failed ({exc.code}).", status=exc.code, body=detail) from exc

        token = (body.get("token") or {}).get("accessToken")
        if not token:
            raise ToastAuthError(f"Authentication response contained no access token: {body}")

        expires_in = int((body.get("token") or {}).get("expiresIn") or 0)
        self._token = token
        self._token_expires_at = time.time() + max(expires_in - _TOKEN_REFRESH_MARGIN_SECONDS, 60)

    def _bearer(self) -> str:
        if self._token is None or time.time() >= self._token_expires_at:
            self._authenticate()
        assert self._token is not None
        return self._token

    # -- requests --------------------------------------------------------

    def get(self, path: str, params: dict | None = None, *, restaurant_guid: str | None = None):
        """GET a Toast endpoint and return the decoded JSON body.

        ``params`` values that are lists become repeated query parameters, which
        is how Toast expects multi-valued filters such as ``timeEntryIds``.
        """
        query = ""
        if params:
            pairs: list[tuple[str, str]] = []
            for key, value in params.items():
                if value is None:
                    continue
                if isinstance(value, (list, tuple)):
                    pairs.extend((key, str(item)) for item in value)
                elif isinstance(value, bool):
                    pairs.append((key, "true" if value else "false"))
                else:
                    pairs.append((key, str(value)))
            if pairs:
                query = "?" + urllib.parse.urlencode(pairs)

        url = f"https://{self.hostname}/{path.lstrip('/')}{query}"
        last_error: Exception | None = None

        for attempt in range(_MAX_ATTEMPTS):
            request = urllib.request.Request(
                url,
                headers={
                    "Authorization": f"Bearer {self._bearer()}",
                    "Toast-Restaurant-External-ID": restaurant_guid or self.restaurant_guid,
                    "Accept": "application/json",
                },
            )
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    raw = response.read()
                    return json.loads(raw) if raw else None
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode(errors="replace")
                if exc.code == 401:
                    # Token may have been revoked or rotated; re-auth once and retry.
                    self._token = None
                    last_error = exc
                    continue
                if exc.code not in _RETRY_STATUSES:
                    raise ToastError(f"GET {path} failed ({exc.code}).", status=exc.code, body=detail) from exc
                last_error = exc
                self._sleep_before_retry(attempt, exc.headers.get("Retry-After"))
            except urllib.error.URLError as exc:
                last_error = exc
                self._sleep_before_retry(attempt, None)

        raise ToastError(f"GET {path} failed after {_MAX_ATTEMPTS} attempts: {last_error}")

    @staticmethod
    def _sleep_before_retry(attempt: int, retry_after: str | None) -> None:
        if retry_after:
            try:
                time.sleep(min(float(retry_after), 60))
                return
            except ValueError:
                pass
        time.sleep(min(2**attempt, 30))

    # -- endpoints -------------------------------------------------------

    def restaurant(self) -> dict:
        """Restaurant configuration, including the business-day cutoff hour."""
        return self.get(f"/restaurants/v1/restaurants/{self.restaurant_guid}")

    def orders(self, start: datetime, end: datetime, *, page_size: int = 100):
        """Yield every order modified in ``[start, end)``, following pagination.

        Toast caps ``pageSize`` at 100 and signals the end of the result set with
        a short or empty page.
        """
        page = 1
        while True:
            batch = self.get(
                "/orders/v2/ordersBulk",
                {
                    "startDate": iso8601(start),
                    "endDate": iso8601(end),
                    "page": page,
                    "pageSize": page_size,
                },
            )
            if not batch:
                return
            yield from batch
            if len(batch) < page_size:
                return
            page += 1

    def orders_for_business_date(self, business_date: str, *, page_size: int = 100):
        """Yield orders promised on one business day, formatted ``yyyymmdd``."""
        page = 1
        while True:
            batch = self.get(
                "/orders/v2/ordersBulk",
                {"businessDate": business_date, "page": page, "pageSize": page_size},
            )
            if not batch:
                return
            yield from batch
            if len(batch) < page_size:
                return
            page += 1

    def time_entries(self, start: datetime, end: datetime, *, include_missed_breaks: bool = True):
        """Yield time entries clocked in during ``[start, end)``.

        Toast rejects windows longer than a month, so a longer span is split into
        28-day chunks transparently.
        """
        window_start = start
        while window_start < end:
            window_end = min(window_start + timedelta(days=28), end)
            batch = self.get(
                "/labor/v1/timeEntries",
                {
                    "startDate": iso8601(window_start),
                    "endDate": iso8601(window_end),
                    "includeMissedBreaks": include_missed_breaks,
                },
            )
            yield from (batch or [])
            window_start = window_end

    def employees(self, *, page_size: int = 100):
        """Yield employee records, following Toast's token-based pagination."""
        page_token = None
        while True:
            params = {"pageSize": page_size}
            if page_token:
                params["pageToken"] = page_token
            batch = self.get("/labor/v1/employees", params)
            if not batch:
                return
            yield from batch
            if len(batch) < page_size:
                return
            # Employees paginate by the GUID of the last record seen.
            page_token = batch[-1].get("guid")
            if not page_token:
                return
