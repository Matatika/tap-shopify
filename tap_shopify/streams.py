"""Stream type classes for tap-shopify."""

from decimal import Decimal
from pathlib import Path
from typing import Optional

from singer_sdk.helpers._classproperty import classproperty
from singer_sdk.typing import JSONTypeHelper

from tap_shopify.client import tap_shopifyStream

SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")


class IPv4Type(JSONTypeHelper):
    """Class for IPv4 type."""

    @classproperty
    def type_dict(cls) -> dict:
        """Define and return the type information."""
        return {
            "type": ["string"],
            "format": ["ipv4"],
        }


class AbandondedCheckouts(tap_shopifyStream):
    """Abandonded checkouts stream."""

    name = "abandonded_checkouts"
    path = "/api/2022-01/checkouts.json"
    records_jsonpath = "$.checkouts[*]"
    primary_keys = ["id"]
    replication_key = None
    schema_filepath = SCHEMAS_DIR / "checkout.json"


class CustomCollections(tap_shopifyStream):
    """Custom collections stream."""

    name = "custom_collections"
    path = "/api/2022-01/custom_collections.json"
    records_jsonpath = "$.custom_collections[*]"
    primary_keys = ["id"]
    replication_key = None
    schema_filepath = SCHEMAS_DIR / "custom_collection.json"


class CollectStream(tap_shopifyStream):
    """Collect stream."""

    name = "collects"
    path = "/api/2022-01/collects.json"
    records_jsonpath = "$.collects[*]"
    primary_keys = ["id"]
    replication_key = None
    schema_filepath = SCHEMAS_DIR / "collect.json"


class CustomersStream(tap_shopifyStream):
    """Customers stream."""

    name = "customers"
    path = "/api/2022-01/customers.json"
    records_jsonpath = "$.customers[*]"
    primary_keys = ["id"]
    replication_key = None
    schema_filepath = SCHEMAS_DIR / "customer.json"


class LocationsStream(tap_shopifyStream):
    """Locations stream."""

    name = "locations"
    path = "/api/2022-01/locations.json"
    records_jsonpath = "$.locations[*]"
    primary_keys = ["id"]
    replication_key = None
    schema_filepath = SCHEMAS_DIR / "location.json"


class MetafieldsStream(tap_shopifyStream):
    """Metafields stream."""

    name = "metafields"
    path = "/api/2022-01/metafields.json"
    records_jsonpath = "$.metafields[*]"
    primary_keys = ["id"]
    replication_key = None
    schema_filepath = SCHEMAS_DIR / "metafield.json"


class OrdersStream(tap_shopifyStream):
    """Orders stream."""

    name = "orders"
    path = "/api/2022-01/orders.json?status=any"
    records_jsonpath = "$.orders[*]"
    primary_keys = ["id"]
    replication_key = None
    schema_filepath = SCHEMAS_DIR / "order.json"

    def post_process(self, row: dict, context: Optional[dict] = None) -> Optional[dict]:
        """Perform syntactic transformations only."""
        super().post_process(row, context)
        row["subtotal_price"] = Decimal(row["subtotal_price"])
        row["total_price"] = Decimal(row["total_price"])
        return row

    def get_child_context(self, record: dict, context: Optional[dict]) -> dict:
        """Return a context dictionary for child streams."""
        return {"order_id": record["id"]}


class ProductsStream(tap_shopifyStream):
    """Products stream."""

    name = "products"
    path = "/api/2022-01/products.json"
    records_jsonpath = "$.products[*]"
    primary_keys = ["id"]
    replication_key = None
    schema_filepath = SCHEMAS_DIR / "product.json"


class TransactionsStream(tap_shopifyStream):
    """Transactions stream."""

    parent_stream_type = OrdersStream

    name = "transactions"
    path = "/api/2022-01/orders/{order_id}/transactions.json"
    records_jsonpath = "$.transactions[*]"
    primary_keys = ["id"]
    replication_key = None
    schema_filepath = SCHEMAS_DIR / "transaction.json"
