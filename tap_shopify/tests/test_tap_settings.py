"""Tests the tap settings."""

import unittest

import responses

import tap_shopify.tests.utils as test_utils
from tap_shopify.client import API_VERSION


class TestTapShopifyWithBaseCredentials(unittest.TestCase):
    """Test class for tap-shopify settings"""

    def setUp(self):
        self.admin_url_mock_config = test_utils.admin_url_mock_config

        responses.reset()

    @responses.activate
    def test_admin_url_setting(self):
        """Test the admin_url tap setting."""

        tap = test_utils.set_up_tap_with_custom_catalog(
            self.admin_url_mock_config, ["customers"]
        )

        # This repsonse url matches the custom admin_url in admin_url_mock_config
        responses.add(
            responses.GET,
            f"https://mock-store.myshopify.com/custom_admin_url/api/{API_VERSION}"
            "/customers.json",
            json=test_utils.customer_return_data,
            status=200,
        )

        tap.sync_all()
