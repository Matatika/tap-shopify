"""Stream type classes for tap-shopify."""

import json
from decimal import Decimal
from pathlib import Path

from tap_shopify import hiddendict
from tap_shopify.client import tap_shopifyStream

SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")


class AbandonedCheckouts(tap_shopifyStream):
    """Abandoned checkouts stream."""

    name = "abandoned_checkouts"
    path = "/checkouts.json"
    records_jsonpath = "$.checkouts[*]"
    primary_keys = ["id"]
    replication_key = "updated_at"
    schema_filepath = SCHEMAS_DIR / "abandoned_checkout.json"


class CollectStream(tap_shopifyStream):
    """Collect stream."""

    name = "collects"
    path = "/collects.json"
    records_jsonpath = "$.collects[*]"
    primary_keys = ["id"]
    replication_key = "id"
    schema_filepath = SCHEMAS_DIR / "collect.json"

    def get_url_params(self, context, next_page_token):
        """Return a dictionary of values to be used in URL parameterization."""
        params = super().get_url_params(context, next_page_token)

        if not next_page_token:
            context_state = self.get_context_state(context)
            last_id = context_state.get("replication_key_value")

            params["since_id"] = last_id

        return params


class CustomCollections(tap_shopifyStream):
    """Custom collections stream."""

    name = "custom_collections"
    path = "/custom_collections.json"
    records_jsonpath = "$.custom_collections[*]"
    primary_keys = ["id"]
    replication_key = "updated_at"
    schema_filepath = SCHEMAS_DIR / "custom_collection.json"


class CustomersStream(tap_shopifyStream):
    """Customers stream."""

    name = "customers"
    path = "/customers.json"
    records_jsonpath = "$.customers[*]"
    primary_keys = ["id"]
    replication_key = "updated_at"
    schema_filepath = SCHEMAS_DIR / "customer.json"


class LocationsStream(tap_shopifyStream):
    """Locations stream."""

    name = "locations"
    path = "/locations.json"
    records_jsonpath = "$.locations[*]"
    primary_keys = ["id"]
    schema_filepath = SCHEMAS_DIR / "location.json"

    def get_child_context(self, record, context):
        """Return a context dictionary for child streams."""
        return {"location_id": record["id"]}


class InventoryLevelsStream(tap_shopifyStream):
    """Inventory levels stream."""

    parent_stream_type = LocationsStream

    name = "inventory_levels"
    path = "/inventory_levels.json"
    records_jsonpath = "$.inventory_levels[*]"
    primary_keys = ["inventory_item_id"]
    schema_filepath = SCHEMAS_DIR / "inventory_level.json"

    def get_child_context(self, record, context):
        """Return a context dictionary for child streams."""
        return {"inventory_item_id": record["inventory_item_id"]}

    def get_url_params(self, context, next_page_token):
        """Return a dictionary of values to be used in URL parameterization."""
        params = super().get_url_params(context, next_page_token)

        if not next_page_token:
            params["location_ids"] = context["location_id"]

        return params


class InventoryItemsStream(tap_shopifyStream):
    """Inventory items stream."""

    parent_stream_type = InventoryLevelsStream

    name = "inventory_items"
    path = "/inventory_items/{inventory_item_id}.json"
    records_jsonpath = "$.inventory_item"
    primary_keys = ["id"]
    schema_filepath = SCHEMAS_DIR / "inventory_item.json"


class MetafieldsStream(tap_shopifyStream):
    """Metafields stream."""

    name = "metafields"
    path = "/metafields.json"
    records_jsonpath = "$.metafields[*]"
    primary_keys = ["id"]
    replication_key = "updated_at"
    schema_filepath = SCHEMAS_DIR / "metafield.json"


class OrdersStream(tap_shopifyStream):
    """Orders stream."""

    name = "orders"
    path = "/orders.json"
    records_jsonpath = "$.orders[*]"
    primary_keys = ["id"]
    replication_key = "updated_at"
    schema_filepath = SCHEMAS_DIR / "order.json"
    is_sorted = True

    def post_process(self, row, context=None):
        """Perform syntactic transformations only."""
        row = super().post_process(row, context)

        if row:
            row["subtotal_price"] = Decimal(row["subtotal_price"])
            row["total_price"] = Decimal(row["total_price"])
        return row

    def get_child_context(self, record, context):
        """Return a context dictionary for child streams."""
        return {
            "order_id": record["id"],
            "order": hiddendict(record),
        }

    def get_url_params(self, context, next_page_token):
        """Return a dictionary of values to be used in URL parameterization."""
        params = super().get_url_params(context, next_page_token)
        params["limit"] = 250

        if not next_page_token:
            params["status"] = "any"
            params["order"] = f"{self.replication_key} asc"

        return params


class _OrderEmbeddedStream(tap_shopifyStream):
    parent_stream_type = OrdersStream
    state_partitioning_keys = []  # do not store any state bookmarks

    def get_records(self, context):
        yield from context["order"][self.name]

    def post_process(self, row, context=None):
        row["order_id"] = context["order_id"]
        return row


class LineItemsStream(_OrderEmbeddedStream):
    """Line items stream (child of orders)."""

    name = "line_items"
    primary_keys = ["id"]
    schema_filepath = SCHEMAS_DIR / "line_item.json"


class ShippingLinesStream(_OrderEmbeddedStream):
    """Shipping lines stream (child of orders)."""

    name = "shipping_lines"
    primary_keys = ["id"]
    schema_filepath = SCHEMAS_DIR / "shipping_line.json"


class TaxLinesStream(_OrderEmbeddedStream):
    """Tax lines stream (child of orders)."""

    name = "tax_lines"
    primary_keys = ["order_id", "title", "rate", "price"]
    schema_filepath = SCHEMAS_DIR / "tax_line.json"


class ProductsStream(tap_shopifyStream):
    """Products stream."""

    name = "products"
    path = "/products.json"
    records_jsonpath = "$.products[*]"
    primary_keys = ["id"]
    replication_key = "updated_at"
    schema_filepath = SCHEMAS_DIR / "product.json"


class TransactionsStream(tap_shopifyStream):
    """Transactions stream."""

    parent_stream_type = OrdersStream

    name = "transactions"
    path = "/orders/{order_id}/transactions.json"
    records_jsonpath = "$.transactions[*]"
    primary_keys = ["id"]
    schema_filepath = SCHEMAS_DIR / "transaction.json"
    state_partitioning_keys = []

    def post_process(self, row, context=None):
        """Attach order context to each transaction."""
        row = super().post_process(row, context)

        if not row:
            return None

        row["order_id"] = context["order_id"] if context else None
        return row


class RefundsStream(_OrderEmbeddedStream):
    """Refunds stream."""

    name = "refunds"
    primary_keys = ["id"]
    schema_filepath = SCHEMAS_DIR / "refund.json"

    def get_child_context(self, record, context):
        """Pass refund context to child streams."""
        return {
            "refund_id": record["id"],
            "refund": hiddendict(record),
        }


class _RefundEmbeddedStream(tap_shopifyStream):
    parent_stream_type = RefundsStream
    state_partitioning_keys = []  # do not store any state bookmarks

    def get_records(self, context):
        yield from context["refund"][self.name]

    def post_process(self, row, context=None):
        row["refund_id"] = context["refund_id"]
        return row


class RefundLineItemsStream(_RefundEmbeddedStream):
    """Refund line items stream (child of refunds)."""

    name = "refund_line_items"
    primary_keys = ["id"]
    schema_filepath = SCHEMAS_DIR / "refund_line_item.json"


class OrderAdjustmentsStream(_RefundEmbeddedStream):
    """Order adjustments stream (child of refunds)."""

    name = "order_adjustments"
    primary_keys = ["id"]
    schema_filepath = SCHEMAS_DIR / "order_adjustment.json"


class UsersStream(tap_shopifyStream):
    """Users stream."""

    name = "users"
    path = "/users.json"
    records_jsonpath = "$.users[*]"
    primary_keys = ["id"]
    schema_filepath = SCHEMAS_DIR / "user.json"


class OrderDiscountCodesStream(_OrderEmbeddedStream):
    """Order discounts stream (child of orders)."""

    name = "order_discount_codes"
    primary_keys = ["order_id", "index"]
    schema_filepath = SCHEMAS_DIR / "order_discount_codes.json"

    def get_records(self, context):
        """Yield each discount code with a 1-based index per order."""
        discount_codes = context["order"].get("discount_codes") or []
        for idx, code in enumerate(discount_codes, start=1):
            if not code:
                continue
            yield {**code, "index": idx}


class GiftCardsStream(tap_shopifyStream):
    """Gift cards stream."""

    name = "gift_cards"
    path = "/gift_cards.json"
    records_jsonpath = "$.gift_cards[*]"
    primary_keys = ["id"]
    replication_key = "updated_at"
    schema_filepath = SCHEMAS_DIR / "gift_cards.json"


class ShopifyQLStream(tap_shopifyStream):
    """Base class for config-driven ShopifyQL query streams.

    -----------------------------------------------------------------------
    DO NOT instantiate or modify this class directly.
    -----------------------------------------------------------------------

    Streams are created at runtime from the `shopifyql_queries` list in the
    tap config. Each entry in that list produces one stream (one table in
    your destination). To add a new ShopifyQL report:

      1. Add an entry to `shopifyql_queries` in meltano.yml (see tap.py for
         the full config schema and field descriptions).
      2. Run `meltano run tap-shopify target-...` — the new table appears
         automatically.

    No changes to this file are needed.

    -----------------------------------------------------------------------
    How ShopifyQL responses are handled
    -----------------------------------------------------------------------
    The Shopify shopifyqlQuery API (2026-04+) returns tabular data: a
    `columns` array of {name, dataType} objects and a `rows` array of
    already-keyed objects. Every value — numbers, dates, booleans — comes
    back as a plain string. Each record looks like:

        {"day": "2024-01-15", "total_sales": "1234.56", ...}

    Type casting (string → float, string → date, etc.) should be done in
    the downstream dbt model or transformation layer, NOT here.

    -----------------------------------------------------------------------
    Primary keys and TOTALS rows
    -----------------------------------------------------------------------
    Queries that use `TIMESERIES day` produce one row per calendar day.
    Queries that also use `WITH TOTALS` append summary rows at the end where
    `day` is null. If your destination rejects null primary keys, add a
    filter to your `primary_keys` or set them to a composite key that
    uniquely identifies each row including summary rows.

    `COMPARE TO previous_period` may add a period-indicator column (e.g.
    `comparison_label`) — include it in `primary_keys` if needed to keep
    rows unique.
    """

    # Set by the dynamic subclass created in tap.py — do not change here.
    name = "shopifyql"
    primary_keys = ["day"]
    replication_key = None  # ShopifyQL is always a full refresh
    schema_filepath = SCHEMAS_DIR / "shopifyql.json"
    http_method = "POST"
    path = "/graphql.json"

    # The ShopifyQL query string, injected per dynamic subclass.
    # Never set this on the base class itself.
    _configured_query: str = ""

    # GraphQL wrapper for the shopifyqlQuery field (API 2026-04+).
    # Double-braces {{ }} are literal braces in the formatted output.
    _GRAPHQL_TEMPLATE = (
        "{{ shopifyqlQuery(query: {shopifyql}) {{"
        " parseErrors"
        " tableData {{ columns {{ name dataType }} rows }}"
        "}} }}"
    )

    def prepare_request_payload(self, context, next_page_token):
        """Build the GraphQL POST body, embedding the ShopifyQL query as a JSON string."""
        graphql = self._GRAPHQL_TEMPLATE.format(
            shopifyql=json.dumps(self._configured_query)
        )
        return {"query": graphql}

    def parse_response(self, response):
        """Unpack the tabular ShopifyQL response into one dict per row."""
        data = response.json()

        gql_errors = data.get("errors")
        if gql_errors:
            raise RuntimeError(f"GraphQL errors: {gql_errors}")

        result = (data.get("data") or {}).get("shopifyqlQuery") or {}

        parse_errors = result.get("parseErrors") or []
        if parse_errors:
            raise RuntimeError(
                f"ShopifyQL parse error in stream '{self.name}': {parse_errors}"
            )

        table_data = result.get("tableData") or {}
        for row in table_data.get("rows") or []:
            yield row

    def get_new_paginator(self):
        """ShopifyQL returns all rows in a single response — no pagination."""
        return None

    def get_url_params(self, context, next_page_token):
        """No query-string params needed; the query goes in the POST body."""
        return {}

    def post_process(self, row, context=None):
        """Return the row as-is — deduplication is not applicable here."""
        return row
