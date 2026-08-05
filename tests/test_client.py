"""Tests for the HTTP client: auth, pagination, retries, and date windowing.

``urlopen`` is stubbed so these run offline and make no real Toast calls.
"""

import io
import json
import sys
import unittest
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from toast.client import ToastAuthError, ToastClient, ToastError, iso8601  # noqa: E402

CONFIG = {
    "hostname": "ws-api.example.com",
    "client_id": "cid",
    "client_secret": "secret",
    "restaurant_guid": "rest-guid",
}

TOKEN_BODY = {"token": {"accessToken": "tok-abc", "expiresIn": 86400}, "status": "SUCCESS"}


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False


def response(payload):
    return FakeResponse(json.dumps(payload).encode())


def http_error(code, retry_after=None):
    headers = {"Retry-After": retry_after} if retry_after else {}
    return urllib.error.HTTPError("https://x", code, "err", headers, io.BytesIO(b"{}"))


class ClientTestCase(unittest.TestCase):
    """Base that records every request the client makes."""

    def setUp(self):
        self.requests = []

    def transport(self, *responses):
        """Return a urlopen stub that replays ``responses`` in order.

        Entries may be payload dicts or exceptions to raise.
        """
        queue = list(responses)

        def fake_urlopen(request, timeout=None):
            self.requests.append(request)
            item = queue.pop(0)
            if isinstance(item, Exception):
                raise item
            return response(item)

        return fake_urlopen


class AuthTests(ClientTestCase):
    def test_token_is_fetched_once_and_reused(self):
        client = ToastClient(**CONFIG)
        with mock.patch("urllib.request.urlopen", self.transport(TOKEN_BODY, [], [])):
            client.get("/a")
            client.get("/b")

        # One login plus two data calls -- the token was cached.
        self.assertEqual(len(self.requests), 3)
        self.assertEqual(self.requests[0].method, "POST")
        self.assertIn("/authentication/v1/authentication/login", self.requests[0].full_url)
        self.assertEqual(self.requests[1].headers["Authorization"], "Bearer tok-abc")

    def test_login_body_uses_machine_client_access_type(self):
        client = ToastClient(**CONFIG)
        with mock.patch("urllib.request.urlopen", self.transport(TOKEN_BODY, [])):
            client.get("/a")

        body = json.loads(self.requests[0].data)
        self.assertEqual(body["userAccessType"], "TOAST_MACHINE_CLIENT")
        self.assertEqual(body["clientId"], "cid")

    def test_restaurant_header_is_sent(self):
        client = ToastClient(**CONFIG)
        with mock.patch("urllib.request.urlopen", self.transport(TOKEN_BODY, [])):
            client.get("/a")

        self.assertEqual(self.requests[1].headers["Toast-restaurant-external-id"], "rest-guid")

    def test_bad_credentials_raise_auth_error(self):
        client = ToastClient(**CONFIG)
        with mock.patch("urllib.request.urlopen", self.transport(http_error(401))):
            with self.assertRaises(ToastAuthError):
                client.get("/a")

    def test_401_on_data_call_triggers_reauth(self):
        client = ToastClient(**CONFIG)
        transport = self.transport(TOKEN_BODY, http_error(401), TOKEN_BODY, [{"guid": "x"}])
        with mock.patch("urllib.request.urlopen", transport):
            result = client.get("/a")

        self.assertEqual(result, [{"guid": "x"}])
        self.assertEqual(len(self.requests), 4)

    def test_missing_config_is_reported_clearly(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(ToastError) as ctx:
                ToastClient()

        self.assertIn("TOAST_HOSTNAME", str(ctx.exception))

    def test_hostname_accepts_a_full_url(self):
        client = ToastClient(**{**CONFIG, "hostname": "https://ws-api.example.com/"})

        self.assertEqual(client.hostname, "ws-api.example.com")


class RetryTests(ClientTestCase):
    def test_rate_limit_is_retried(self):
        client = ToastClient(**CONFIG)
        transport = self.transport(TOKEN_BODY, http_error(429, "0"), [{"guid": "x"}])
        with mock.patch("urllib.request.urlopen", transport), mock.patch("time.sleep"):
            result = client.get("/a")

        self.assertEqual(result, [{"guid": "x"}])

    def test_client_errors_are_not_retried(self):
        client = ToastClient(**CONFIG)
        with mock.patch("urllib.request.urlopen", self.transport(TOKEN_BODY, http_error(400))):
            with self.assertRaises(ToastError) as ctx:
                client.get("/a")

        self.assertEqual(ctx.exception.status, 400)
        self.assertEqual(len(self.requests), 2)

    def test_gives_up_after_max_attempts(self):
        client = ToastClient(**CONFIG)
        transport = self.transport(TOKEN_BODY, *[http_error(503) for _ in range(5)])
        with mock.patch("urllib.request.urlopen", transport), mock.patch("time.sleep"):
            with self.assertRaises(ToastError):
                client.get("/a")


class PaginationTests(ClientTestCase):
    def test_orders_follow_pages_until_short_page(self):
        full = [{"guid": f"o{i}"} for i in range(100)]
        transport = self.transport(TOKEN_BODY, full, [{"guid": "last"}])
        client = ToastClient(**CONFIG)

        with mock.patch("urllib.request.urlopen", transport):
            orders = list(client.orders(datetime(2026, 8, 1), datetime(2026, 8, 2)))

        self.assertEqual(len(orders), 101)
        self.assertIn("page=1", self.requests[1].full_url)
        self.assertIn("page=2", self.requests[2].full_url)

    def test_orders_stop_on_empty_first_page(self):
        client = ToastClient(**CONFIG)
        with mock.patch("urllib.request.urlopen", self.transport(TOKEN_BODY, [])):
            orders = list(client.orders(datetime(2026, 8, 1), datetime(2026, 8, 2)))

        self.assertEqual(orders, [])
        self.assertEqual(len(self.requests), 2)

    def test_time_entries_split_long_ranges_into_windows(self):
        client = ToastClient(**CONFIG)
        transport = self.transport(TOKEN_BODY, [{"guid": "t1"}], [{"guid": "t2"}], [{"guid": "t3"}])

        with mock.patch("urllib.request.urlopen", transport):
            entries = list(client.time_entries(datetime(2026, 1, 1), datetime(2026, 3, 1)))

        # 59 days across a 28-day cap is three requests, none over Toast's month limit.
        self.assertEqual(len(entries), 3)
        self.assertEqual(len(self.requests), 4)

    def test_short_range_is_a_single_request(self):
        client = ToastClient(**CONFIG)
        with mock.patch("urllib.request.urlopen", self.transport(TOKEN_BODY, [])):
            list(client.time_entries(datetime(2026, 8, 1), datetime(2026, 8, 8)))

        self.assertEqual(len(self.requests), 2)


class QueryEncodingTests(ClientTestCase):
    def test_lists_become_repeated_parameters(self):
        client = ToastClient(**CONFIG)
        with mock.patch("urllib.request.urlopen", self.transport(TOKEN_BODY, [])):
            client.get("/labor/v1/timeEntries", {"timeEntryIds": ["a", "b"]})

        self.assertIn("timeEntryIds=a&timeEntryIds=b", self.requests[1].full_url)

    def test_booleans_are_lowercased_and_nones_dropped(self):
        client = ToastClient(**CONFIG)
        with mock.patch("urllib.request.urlopen", self.transport(TOKEN_BODY, [])):
            client.get("/x", {"flag": True, "skip": None})

        url = self.requests[1].full_url
        self.assertIn("flag=true", url)
        self.assertNotIn("skip", url)


class DateFormatTests(unittest.TestCase):
    def test_millisecond_precision_and_offset(self):
        moment = datetime(2016, 1, 1, 14, 13, 12, 456789, tzinfo=timezone.utc)

        self.assertEqual(iso8601(moment), "2016-01-01T14:13:12.456+0000")

    def test_naive_datetimes_are_read_as_utc(self):
        self.assertTrue(iso8601(datetime(2026, 8, 4)).endswith("+0000"))


if __name__ == "__main__":
    unittest.main()
