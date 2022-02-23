"""Tests standard tap features using the built-in SDK tests library."""

import datetime

from singer_sdk.testing import get_standard_tap_tests

from tap_shopify.tap import Taptap_shopify

SAMPLE_CONFIG = {
    "access_token": "mock-token",
    "store": "mock-store",
    "start_date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
}

# Run standard built-in tap tests from the SDK:
def test_standard_tap_tests():
    """Run standard tap tests from the SDK."""
    tests = get_standard_tap_tests(
        Taptap_shopify,
        config=SAMPLE_CONFIG
    )
    for test in tests:
        test()


# TODO: Create additional tests as appropriate for your tap.
