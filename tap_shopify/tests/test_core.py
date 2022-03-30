"""Tests standard tap features using the built-in SDK tests library."""

import datetime
import unittest

import responses
from singer_sdk.testing import get_standard_tap_tests

from tap_shopify.tap import Tap_Shopify

SAMPLE_CONFIG = {
    "access_token": "mock-token",
    "store": "mock-store",
    "start_date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"),
}


class TestCore(unittest.TestCase):
    """Test class for core tap tests"""

    def setUp(self):
        # reset mock responses
        responses.reset()

    # Run standard built-in tap tests from the SDK:
    @responses.activate()
    def test_standard_tap_tests(self):
        """Run standard tap tests from the SDK."""
        # given a mock response to the standard stream test
        responses.add(
            responses.GET,
            "https://mock-store.myshopify.com/admin/api/2022-01/orders.json?status=any",
            json={},
            status=200,
        )
        responses.add(
            responses.GET,
            "https://mock-store.myshopify.com/admin/api/2022-01/products.json",
            json={},
            status=200,
        )
        responses.add(
            responses.GET,
            "https://mock-store.myshopify.com/admin/api/2022-01/customers.json",
            json={},
            status=200,
        )
        responses.add(
            responses.GET,
            "https://mock-store.myshopify.com/admin/api/2022-01/locations.json",
            json={},
            status=200,
        )
        responses.add(
            responses.GET,
            "https://mock-store.myshopify.com/admin/api/2022-01/collects.json",
            json={},
            status=200,
        )
        responses.add(
            responses.GET,
            "https://mock-store.myshopify.com/admin/api/2022-01/checkouts.json",
            json={},
            status=200,
        )
        responses.add(
            responses.GET,
            "https://mock-store.myshopify.com/"
            + "admin/api/2022-01/custom_collections.json",
            json={},
            status=200,
        )
        responses.add(
            responses.GET,
            "https://mock-store.myshopify.com/admin/api/2022-01/metafields.json",
            json={},
            status=200,
        )
        responses.add(
            responses.GET,
            "https://mock-store.myshopify.com/admin/api/2022-01/transactions.json",
            json={},
            status=200,
        )

        # when run standard tests
        tests = get_standard_tap_tests(Tap_Shopify, config=SAMPLE_CONFIG)
        # expect no failures
        for test in tests:
            test()
