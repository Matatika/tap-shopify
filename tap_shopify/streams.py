"""Stream type classes for tap-shopify."""

import json
import logging
import re
from decimal import Decimal
from functools import cached_property
from pathlib import Path

import requests
from singer_sdk import typing as th
from singer_sdk.exceptions import FatalAPIError, RetriableAPIError
from singer_sdk.pagination import BaseOffsetPaginator
from typing_extensions import override

from tap_shopify import hiddendict
from tap_shopify.client import tap_shopifyStream

SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")

logger = logging.getLogger(__name__)


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


class _ShopifyQLPaginator(BaseOffsetPaginator):
    """Pages through a ShopifyQL response using LIMIT/OFFSET.

    The `shopifyqlQuery` field has no cursor or `pageInfo` — it caps every
    response at `page_size` rows (1,000 by default) with no error or
    indication that results were truncated. Shopify's own guidance (see
    ShopifyQLStream's docstring) is to page through results by re-issuing the
    query with `LIMIT <page_size> OFFSET <n * page_size>` until a response
    comes back with fewer than `page_size` rows.

    `max_pages` is a safety valve, not an expected limit: it stops an
    unexpectedly large backlog from paginating for an unbounded number of
    requests in one sync. Hitting it is logged as a warning, not an error —
    the stream's bookmark still only advances to the last fully-fetched
    page, so remaining data is picked up on the next incremental run.
    """

    def __init__(self, start_value, page_size, max_pages, stream_name):
        super().__init__(start_value, page_size)
        self._max_pages = max_pages
        self._stream_name = stream_name

    def has_more(self, response) -> bool:
        """Continue while the last page was full and under the page cap."""
        if self.count >= self._max_pages:
            logger.warning(
                "ShopifyQL stream '%s' hit its %d-page pagination safety "
                "cap at offset %d without exhausting results for this sync "
                "window; the remainder will be fetched on a later run.",
                self._stream_name,
                self._max_pages,
                self.current_value,
            )
            return False

        result = (response.json().get("data") or {}).get("shopifyqlQuery") or {}
        rows = (result.get("tableData") or {}).get("rows") or []
        return len(rows) >= self._page_size


class ShopifyQLStream(tap_shopifyStream):
    """Base class for config-driven ShopifyQL query streams.

    Instantiate via tap.py by passing the query config entry as a kwarg:

        ShopifyQLStream(tap=self, query=entry)

    where `entry` is a dict with keys `name`, `query`, and optionally
    `primary_keys`. One instance = one destination table.

    -----------------------------------------------------------------------
    Adding a new ShopifyQL report
    -----------------------------------------------------------------------
    Add an entry to `shopifyql_queries` in meltano.yml (see tap.py for the
    full config schema). No changes to this file are needed.

    -----------------------------------------------------------------------
    Schema discovery
    -----------------------------------------------------------------------
    The Singer schema is built by making a real API request with a
    constrained 1-day window and reading the column metadata from the
    response. All values are typed as StringType (Shopify returns everything
    as strings — cast to numeric/date types in dbt).

    -----------------------------------------------------------------------
    Incremental sync
    -----------------------------------------------------------------------
    If the query contains a TIMESERIES clause, the TIMESERIES column (e.g.
    "day") is used as the replication key. On subsequent runs the SINCE
    clause is updated (or injected if absent) with the last synced value
    from state so only new rows are fetched. On the first run the query is
    used as-is.

    Queries without a TIMESERIES clause are always full-refresh.

    -----------------------------------------------------------------------
    Pagination
    -----------------------------------------------------------------------
    `shopifyqlQuery` defaults to returning at most 1,000 rows per request
    and offers no cursor-based pagination — but Shopify's Admin API team has
    confirmed (shopify.dev / Shopify Developer Community, Oct 2025) that a
    query's own `LIMIT`/`OFFSET` clauses are the supported way to page
    through a larger result set, the same syntax used by Shopify's Analytics
    query editor. Any `LIMIT`/`OFFSET` written in the configured query is
    replaced each request with one reflecting the current page; see
    `PAGE_SIZE` / `MAX_PAGES_PER_SYNC` below to tune paging behavior.

    Without this, a query spanning more rows than one page silently drops
    everything past the first page — mid-day, if that's where the row count
    happens to land — with no error raised.

    IMPORTANT — ORDER BY must be fully deterministic for paginating queries.
    `ORDER BY day ASC` alone only sorts by day; if a day has more rows than
    fit in one page, LIMIT/OFFSET has no defined tie-break for rows sharing
    that day; the same row can then be returned on both sides of a page
    boundary (verified directly: this produced 64 duplicate rows across two
    live pages). The fix is to ORDER BY every GROUP BY column, not just the
    TIMESERIES one — e.g. `ORDER BY day ASC, order_id ASC, line_item_id ASC,
    ...` for every column in the query's GROUP BY clause. Since GROUP BY
    guarantees each such combination appears in at most one output row, this
    guarantees no ties are possible (confirmed directly: zero overlap across
    pages with a fully-specified ORDER BY, vs. 64 duplicate rows without
    one). A query with no GROUP BY (e.g. one row per TIMESERIES value, like
    a simple daily rollup) doesn't need this — ORDER BY on the TIMESERIES
    column alone is already unique per row in that case.
    """

    schema_filepath = None  # schema is discovered dynamically via API
    http_method = "POST"
    path = "/graphql.json"

    # Rows requested per page. Shopify's own default/recommendation when
    # paging via LIMIT/OFFSET (see the "Pagination" docstring section above).
    PAGE_SIZE = 1000

    # Safety cap on pages fetched in a single sync (see _ShopifyQLPaginator).
    # 50 pages * 1,000 rows = 50,000 rows per run before deferring the rest
    # to the next incremental run.
    MAX_PAGES_PER_SYNC = 50

    # Retry budget for THROTTLED responses (see validate_response/
    # backoff_max_tries below). The SDK's default of 5 tries gives ~30s of
    # cumulative backoff with the default exponential wait generator, which
    # is not enough: a single wide-range ShopifyQL query can consume nearly
    # the entire 1,000-point GraphQL cost bucket in one call (confirmed
    # directly against the live API), and recovering needs enough backoff to
    # span Shopify's bucket-reset window — observed directly to take
    # ~60-90s. Confirmed live in production: the default budget was
    # exhausted mid-backoff (2.7s, 5.0s, 8.4s, 16.5s, ~33s total) before the
    # window reset, and the pipeline failed outright.
    BACKOFF_MAX_TRIES = 7

    # Matches a LIMIT clause and its optional trailing OFFSET, so a
    # user-authored LIMIT/OFFSET in the configured query can be replaced
    # with the current page's values rather than conflicting with them.
    _LIMIT_OFFSET_RE = re.compile(r"\bLIMIT\s+\d+(?:\s+OFFSET\s+\d+)?", re.IGNORECASE)
    # VISUALIZE is a trailing rendering directive, not part of the query
    # pipeline — LIMIT/OFFSET must be inserted before it, not after.
    _VISUALIZE_RE = re.compile(r"\bVISUALIZE\b.*\Z", re.IGNORECASE | re.DOTALL)

    @override
    @property
    def is_sorted(self) -> bool:
        """Return True if the stream has a replication key configured."""
        return bool(self.replication_key)

    # GraphQL wrapper for the shopifyqlQuery field (API 2025-10+).
    # Double-braces {{ }} are literal braces in the formatted output.
    _GRAPHQL_TEMPLATE = (
        "{{ shopifyqlQuery(query: {shopifyql}) {{"
        " parseErrors"
        " tableData {{ columns {{ name dataType }} rows }}"
        "}} }}"
    )

    def __init__(self, *args, **kwargs):
        """Initialize the stream from a shopifyql_queries config entry."""
        query_entry = kwargs.pop("query")
        self.name = query_entry["name"]
        self._configured_query = query_entry["query"]

        super().__init__(*args, **kwargs)

        # Must be set after super().__init__(), which resets
        # self._primary_keys / self._replication_key to their defaults.
        self.primary_keys = query_entry.get("primary_keys") or []
        self.replication_key = query_entry.get("replication_key")

    @cached_property
    def schema(self) -> dict:
        """Discover schema by probing the API with a 1-day window."""
        probe_query = re.sub(
            r"\b(SINCE|UNTIL)\s+\S+",
            "",
            self._configured_query,
            flags=re.IGNORECASE,
        ).strip()
        probe_query += " SINCE -1d UNTIL -0d"

        graphql = self._GRAPHQL_TEMPLATE.format(shopifyql=json.dumps(probe_query))
        response = requests.post(
            self.url_base + self.path,
            json={"query": graphql},
            headers={"X-Shopify-Access-Token": self.config["access_token"]},
        )
        self.validate_response(response)
        query: dict = response.json()["data"]["shopifyqlQuery"]

        # https://shopify.dev/docs/api/admin-graphql/2025-10/objects/ShopifyqlTableData
        columns = query["tableData"]["columns"] if "tableData" in query else []

        props = [
            th.Property(
                col["name"],
                (
                    th.DateTimeType
                    if col["name"] == self.replication_key
                    else th.StringType
                ),
            )
            for col in columns
        ]
        return th.PropertiesList(*props).to_dict()

    def prepare_request_payload(self, context, next_page_token):
        """Build the GraphQL POST body, injecting state and paging into the query."""
        query = self._configured_query

        # Inject or replace SINCE using the starting timestamp, which resolves
        # to the last state value on incremental runs or start_date on first run.
        starting_ts = self.get_starting_timestamp(context)
        if starting_ts:
            since_date = starting_ts.date().isoformat()
            if re.search(r"\bSINCE\b", query, re.IGNORECASE):
                query = re.sub(
                    r"\bSINCE\s+\S+",
                    f"SINCE {since_date}",
                    query,
                    flags=re.IGNORECASE,
                )
            else:
                query = query.rstrip() + f" SINCE {since_date}"

        offset = next_page_token or 0
        query = self._paginated_query(query, self.PAGE_SIZE, offset)

        graphql = self._GRAPHQL_TEMPLATE.format(shopifyql=json.dumps(query))
        return {"query": graphql}

    @override
    def validate_response(self, response):
        """Validate the response, retrying Shopify's in-body GraphQL throttling.

        `shopifyqlQuery` returns HTTP 200 even when throttled — the
        THROTTLED error only appears inside the GraphQL response body, so
        the SDK's default status-code-based retry logic never sees it.
        Checked first, before the blanket GraphQL-error check below, so a
        throttled page backs off and retries instead of raising an
        unretried, fatal error — which pagination makes considerably more
        likely to occur.
        """
        super().validate_response(response)

        data: dict = response.json()

        # https://shopify.dev/docs/api/admin-graphql/2025-10#status-and-error-codes
        if gql_errors := data.get("errors"):
            for error in gql_errors:
                if (error.get("extensions") or {}).get("code") == "THROTTLED":
                    raise RetriableAPIError(
                        f"ShopifyQL query throttled for stream '{self.name}': "
                        f"{error.get('message')}",
                        response,
                    )
            raise FatalAPIError(f"GraphQL errors: {gql_errors}")

        # https://shopify.dev/docs/api/admin-graphql/2025-10/objects/ShopifyqlQueryResponse
        query: dict = data["data"]["shopifyqlQuery"]

        if parse_errors := query["parseErrors"]:
            raise FatalAPIError(f"ShopifyQL parse errors: {parse_errors}")

    @classmethod
    def _paginated_query(cls, query: str, limit: int, offset: int) -> str:
        """Return `query` with a fresh LIMIT/OFFSET for the given page.

        Any LIMIT/OFFSET already in the query is replaced rather than
        stacked, and the new clause is placed before a trailing VISUALIZE
        directive (if any) since VISUALIZE must be the last clause.
        """
        query = cls._LIMIT_OFFSET_RE.sub("", query)

        visualize_match = cls._VISUALIZE_RE.search(query)
        visualize_clause = ""
        if visualize_match:
            visualize_clause = " " + visualize_match.group(0).strip()
            query = query[: visualize_match.start()]

        query = query.rstrip() + f" LIMIT {limit} OFFSET {offset}"
        query = re.sub(r"[ \t]{2,}", " ", query)
        return query + visualize_clause

    def parse_response(self, response):
        """Unpack the tabular ShopifyQL response into one dict per row."""
        query: dict = response.json()["data"]["shopifyqlQuery"]

        # https://shopify.dev/docs/api/admin-graphql/2025-10/objects/ShopifyqlTableData#field-ShopifyqlTableData
        yield from (query["tableData"]["rows"] if "tableData" in query else [])

    def get_new_paginator(self):
        """Page through results via LIMIT/OFFSET (see the class docstring)."""
        return _ShopifyQLPaginator(
            start_value=0,
            page_size=self.PAGE_SIZE,
            max_pages=self.MAX_PAGES_PER_SYNC,
            stream_name=self.name,
        )

    def get_url_params(self, context, next_page_token):
        """No query-string params needed; the query goes in the POST body."""
        return {}

    def backoff_max_tries(self) -> int:
        """Widen the retry budget so backoff can span Shopify's throttle window.

        See BACKOFF_MAX_TRIES above for why the SDK's default (5) isn't
        enough for this stream specifically.
        """
        return self.BACKOFF_MAX_TRIES

    def post_process(self, row, context=None):
        """Normalize the replication key to a full timestamp.

        ShopifyQL returns date-only strings (e.g. "2026-07-03") for TIMESERIES
        columns, but the declared date-time schema type — and BigQuery's
        TIMESTAMP column type on load — require a full timestamp value.
        """
        if self.replication_key and self.replication_key in row:
            value = row[self.replication_key]
            if isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
                row[self.replication_key] = f"{value}T00:00:00Z"
        return row
