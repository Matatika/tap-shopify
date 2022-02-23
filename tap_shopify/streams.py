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

class CurrencyAmount(JSONTypeHelper):
    @classproperty
    def type_dict(cls) -> dict:
        return {
            "type": ["string"],
            "pattern": ["^(0|([1-9]+[0-9]*))(\.[0-9]{1,2})?$"],
            "minLength": 1,
        }

class ProductsStream(tap_shopifyStream):
    """Products stream."""
    name = "products"
    path = "/api/2022-01/products.json"
    records_jsonpath = "$.products[*]"
    primary_keys = ["id"]
    replication_key = None
    schema = th.PropertiesList(
        th.Property(
            "id",
            th.IntegerType,
            description="The product system ID"
        ),
        th.Property("title", th.StringType),
        th.Property("vendor", th.StringType),
        th.Property("product_type", th.StringType),
        th.Property("created_at", th.DateTimeType),
        th.Property("handle", th.StringType),
        th.Property("updated_at", th.DateTimeType),
        th.Property("published_at", th.DateTimeType),
        th.Property("published_scope", th.StringType),
        th.Property("tags", th.StringType),
    ).to_dict()

class OrdersStream(tap_shopifyStream):
    """Orders stream."""
    name = "orders"
    path = "/api/2022-01/orders.json?status=any"
    records_jsonpath = "$.orders[*]"
    primary_keys = ["id"]
    replication_key = None
    schema = th.PropertiesList(
        th.Property(
            "id",
            th.IntegerType,
            description="The order system ID"
        ),
        th.Property("app_id", th.IntegerType),
        th.Property("browser_ip", IPv4Type),
        th.Property("buyer_accepts_marketing", th.BooleanType),
        th.Property("cancel_reason", th.StringType),
        th.Property("cancelled_at", th.DateTimeType),
        th.Property("cart_token", th.StringType),
        th.Property("checkout_id", th.IntegerType),
        th.Property("checkout_token", th.StringType),
        th.Property("closed_at", th.DateTimeType),
        th.Property("confirmed", th.BooleanType),
        th.Property("contact_email", th.StringType),
        th.Property("created_at", th.DateTimeType),
        th.Property("currency", th.StringType),
        th.Property("customer_locale", th.StringType),
        th.Property("device_id", th.StringType),
        th.Property("total_price", CurrencyAmount),
    ).to_dict()

