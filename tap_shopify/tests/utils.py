"""Utilities used in this module."""

from datetime import datetime

from singer_sdk._singerlib.catalog import Catalog
from singer_sdk.helpers import _catalog

from tap_shopify.tap import Tap_Shopify

basic_mock_config = {"access_token": "1234", "store": "mock-store"}

admin_url_mock_config = {
    "access_token": "1234",
    "store": "mock-store",
    "admin_url": "https://mock-store.myshopify.com/custom_admin_url",
}

customer_return_data = {
    "customers": [
        {
            "id": "1234567890",
            "updated_at": datetime.now().isoformat(),
        }
    ]
}

product_return_data = {
    "products": [
        {
            "id": "1234567890",
            "updated_at": datetime.now().isoformat(),
        }
    ]
}


def set_up_tap_with_custom_catalog(mock_config, stream_list):
    """Create an instance of tap-spotify with specific config and streams."""
    tap = Tap_Shopify(config=mock_config)
    # Run discovery
    tap.run_discovery()
    # Get catalog from tap
    catalog = Catalog.from_dict(tap.catalog_dict)
    # Reset and re-initialize with an input catalog
    _catalog.deselect_all_streams(catalog=catalog)
    for stream in stream_list:
        _catalog.set_catalog_stream_selected(
            catalog=catalog,
            stream_name=stream,
            selected=True,
        )
    # Initialise tap with new catalog
    return Tap_Shopify(config=mock_config, catalog=catalog.to_dict())
