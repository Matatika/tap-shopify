"""Tests the tap settings."""

import unittest

import responses
import singer

import tap_shopify.tests.utils as test_utils


class TestTapShopifyWithBaseCredentials(unittest.TestCase):
    """Test class for tap-shopify settings"""

    def setUp(self):
        self.basic_mock_config = test_utils.basic_mock_config

        responses.reset()
        del test_utils.SINGER_MESSAGES[:]

        singer.write_message = test_utils.accumulate_singer_messages

    @responses.activate
    def test_pagination(self):

        tap = test_utils.set_up_tap_with_custom_catalog(
            self.basic_mock_config, ["products"]
        )

        responses.add(
            responses.GET,
            "https://mock-store.myshopify.com/" + "admin/api/2022-01/products.json",
            json=test_utils.customer_return_data,
            status=200,
            headers={
                "link": "<https://mock-store.myshopify.com/"
                + "admin/api/2022-1/products.json?limit=1?page_info=12345}>; rel=next}"
            },
        )

        responses.add(
            responses.GET,
            "https://mock-store.myshopify.com"
            + "/admin/api/2022-1/products.json?limit=1?page_info=12345",
            status=200,
        )

        tap.sync_all()

        self.assertEqual(len(test_utils.SINGER_MESSAGES), 2)
        self.assertIsInstance(test_utils.SINGER_MESSAGES[0], singer.SchemaMessage)
        self.assertIsInstance(test_utils.SINGER_MESSAGES[1], singer.StateMessage)
