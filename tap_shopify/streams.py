"""Stream type classes for tap-shopify."""

from pathlib import Path
from typing import Any, Dict, Optional, Union, List, Iterable

from singer_sdk import typing as th  # JSON Schema typing helpers
from singer_sdk.helpers._classproperty import classproperty
from singer_sdk.typing import JSONTypeHelper

from tap_shopify.client import tap_shopifyStream

SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")

class IPv4Type(JSONTypeHelper):
    @classproperty
    def type_dict(cls) -> dict:
        return {
            "type": ["string"],
            "format": ["ipv4"],
        }

class ProductsStream(tap_shopifyStream):
    """Products stream."""
    name = "products"
    path = "/api/2022-01/products.json"
    records_jsonpath = "$.products[*]"
    primary_keys = ["id"]
    replication_key = None
    schema_filepath = SCHEMAS_DIR / "product.json"

class OrdersStream(tap_shopifyStream):
    """Orders stream."""
    name = "orders"
    path = "/api/2022-01/orders.json?status=any"
    records_jsonpath = "$.orders[*]"
    primary_keys = ["id"]
    replication_key = None
    schema_filepath = SCHEMAS_DIR / "order.json"

