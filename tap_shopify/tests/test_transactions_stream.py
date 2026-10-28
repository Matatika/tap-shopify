"""Tests that TransactionsStream never applies a created_at_min/updated_at_min filter.

Regression test for https://github.com/Matatika/tap-shopify/issues/26: this stream
declares no `replication_key`, so it can never earn a bookmark. Falling through to
the base client's `created_at_min`/`updated_at_min` logic would silently drop any
transaction older than the tap's static `start_date`, forever, even on orders that
were correctly re-visited via the parent OrdersStream's own `updated_at` cursor.
"""

import unittest
from urllib.parse import parse_qs, urlparse

import responses

import tap_shopify.tests.utils as test_utils
from tap_shopify.client import API_VERSION

order_return_data = {
    "orders": [
        {
            "id": 111,
            "updated_at": "2026-09-01T00:00:00Z",
            "subtotal_price": "10.00",
            "total_price": "10.00",
        }
    ]
}


class TestTransactionsStream(unittest.TestCase):
    """Test class for TransactionsStream's URL params."""

    def setUp(self):
        # A configured start_date is what triggers the base class's cold-start
        # `created_at_min` fallback -- without one, this stream would pass even
        # on the old, unfixed code.
        self.mock_config = {
            **test_utils.basic_mock_config,
            "start_date": "2018-01-01T00:00:00Z",
        }

        responses.reset()

    @responses.activate
    def test_transactions_request_has_no_date_filter(self):
        """Assert the transactions sub-request carries no date-filter params."""

        tap = test_utils.set_up_tap_with_custom_catalog(
            self.mock_config, ["orders", "transactions"]
        )

        orders_url = (
            f"https://mock-store.myshopify.com/admin/api/{API_VERSION}/orders.json"
        )
        transactions_url = (
            "https://mock-store.myshopify.com/admin/api/"
            f"{API_VERSION}/orders/111/transactions.json"
        )

        responses.add(responses.GET, orders_url, json=order_return_data, status=200)
        # `responses` matches on path only when the registered URL has no
        # querystring, so this matches the request regardless of what params
        # the (possibly unfixed) code appends.
        responses.add(
            responses.GET, transactions_url, json={"transactions": []}, status=200
        )

        tap.sync_all()

        transactions_calls = [
            call
            for call in responses.calls
            if urlparse(call.request.url).path.endswith("/orders/111/transactions.json")
        ]
        self.assertEqual(len(transactions_calls), 1)

        query_params = parse_qs(urlparse(transactions_calls[0].request.url).query)
        self.assertNotIn("created_at_min", query_params)
        self.assertNotIn("updated_at_min", query_params)
