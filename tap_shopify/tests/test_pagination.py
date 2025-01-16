"""Tests the tap settings."""

import unittest

import responses

import tap_shopify.tests.utils as test_utils
from tap_shopify.client import API_VERSION


class TestTapShopifyWithBaseCredentials(unittest.TestCase):
    """Test class for tap-shopify settings"""

    def setUp(self):
        self.basic_mock_config = test_utils.basic_mock_config

        responses.reset()

    @responses.activate
    def test_pagination(self):
        tap = test_utils.set_up_tap_with_custom_catalog(
            self.basic_mock_config, ["products"]
        )

        resource_url = (
            f"https://mock-store.myshopify.com/admin/api/{API_VERSION}/products.json"
        )

        rsp1 = responses.Response(
            responses.GET,
            resource_url,
            json=test_utils.product_return_data,
            status=200,
            headers={"link": f"{resource_url}?limit=1&page_info=12345; rel=next"},
        )

        rsp2 = responses.Response(
            responses.GET,
            f"{resource_url}?limit=1&page_info=12345",
            json=test_utils.product_return_data,
            status=200,
            headers={"link": f"{resource_url}?limit=1&page_info=12346; rel=next"},
        )

        rsp3 = responses.Response(
            responses.GET,
            f"{resource_url}?limit=1&page_info=12346",
            json=test_utils.product_return_data,
            status=200,
        )

        responses.add(rsp1)
        responses.add(rsp2)
        responses.add(rsp3)

        tap.sync_all()

        self.assertIs(rsp1.call_count, 1)
        self.assertIs(rsp2.call_count, 1)
        self.assertIs(rsp3.call_count, 1)
