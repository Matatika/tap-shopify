"""tap_shopify tap class."""

from typing import List

from singer_sdk import Stream, Tap
from singer_sdk import typing as th  # JSON schema typing helpers

# Import stream types
from tap_shopify.streams import (
    AbandonedCheckouts,
    CollectStream,
    CustomCollections,
    CustomersStream,
    GiftCardsStream,
    InventoryItemsStream,
    InventoryLevelsStream,
    LineItemsStream,
    LocationsStream,
    MetafieldsStream,
    OrderAdjustmentsStream,
    OrderDiscountCodesStream,
    OrdersStream,
    ProductsStream,
    RefundLineItemsStream,
    RefundsStream,
    ShippingLinesStream,
    ShopifyQLStream,
    TaxLinesStream,
    TransactionsStream,
    UsersStream,
)

STREAM_TYPES = [
    AbandonedCheckouts,
    CollectStream,
    CustomCollections,
    CustomersStream,
    InventoryItemsStream,
    InventoryLevelsStream,
    LocationsStream,
    MetafieldsStream,
    OrdersStream,
    LineItemsStream,
    ShippingLinesStream,
    TaxLinesStream,
    RefundsStream,
    RefundLineItemsStream,
    OrderAdjustmentsStream,
    ProductsStream,
    TransactionsStream,
    OrderDiscountCodesStream,
    GiftCardsStream,
]


class Tap_Shopify(Tap):
    """tap_shopify tap class."""

    name = "tap-shopify"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "access_token",
            th.StringType,
            required=True,
            description="The access token to authenticate with the Shopify API",
        ),
        th.Property(
            "store",
            th.StringType,
            required=True,
            description=(
                "Shopify store id, use the prefix of your admin url "
                "e.g. https://[your store].myshopify.com/admin"
            ),
        ),
        th.Property(
            "start_date",
            th.DateTimeType,
            description="The earliest record date to sync",
        ),
        th.Property(
            "admin_url",
            th.StringType,
            description=(
                "The Admin url for your Shopify store (overrides 'store' property)"
            ),
        ),
        th.Property(
            "is_plus_account",
            th.BooleanType,
            description="Enabled Shopify plus account endpoints.",
        ),
        th.Property(
            "shopifyql_queries",
            th.ArrayType(
                th.ObjectType(
                    th.Property(
                        "name",
                        th.StringType,
                        required=True,
                        description=(
                            "Stream name — becomes the table name in your destination "
                            "(e.g. 'sales_over_time' produces a table called "
                            "'sales_over_time'). "
                            "Use lowercase letters, numbers, and underscores only. "
                            "IMPORTANT: treat this as immutable after the first sync. "
                            "Renaming it is a breaking change — the old table is "
                            "orphaned and a new empty table is created."
                        ),
                    ),
                    th.Property(
                        "query",
                        th.StringType,
                        required=True,
                        description=(
                            "The full ShopifyQL query string to run. "
                            "Write it exactly as you would in the Shopify Analytics "
                            "query editor. The tap sends this verbatim to the "
                            "shopifyqlQuery GraphQL API — no modifications are made. "
                            "Example: "
                            "'FROM sales "
                            "SHOW orders, gross_sales, net_sales, total_sales "
                            "TIMESERIES day "
                            "SINCE 2024-01-01 UNTIL today "
                            "ORDER BY day ASC "
                            "LIMIT 1000'. "
                            "Notes: "
                            "(1) SINCE/UNTIL dates control the reporting window — "
                            "the tap does not inject start_date into the query "
                            "automatically, so set the date range explicitly here. "
                            "(2) Every value in the response is returned as a string. "
                            "Cast to numeric/date types in your dbt models. "
                            "(3) TIMESERIES day produces one row per day; "
                            "WITH TOTALS appends summary rows where 'day' is null. "
                            "(4) COMPARE TO previous_period may add a "
                            "period-indicator column — account for it in primary_keys "
                            "if rows would otherwise collide."
                        ),
                    ),
                    th.Property(
                        "primary_keys",
                        th.ArrayType(th.StringType),
                        description=(
                            "List of column names that uniquely identify a row. "
                            "Defaults to ['day'] if omitted, which is correct for "
                            "most TIMESERIES queries without COMPARE TO. "
                            "If your query uses COMPARE TO previous_period, the "
                            "same day appears in both periods — add the "
                            "period-indicator column here to avoid collisions "
                            "(e.g. ['day', 'comparison_label']). "
                            "If your query has no time dimension at all, set this "
                            "to a column that is unique per row, or omit it and "
                            "accept that the destination will upsert on 'day'."
                        ),
                    ),
                )
            ),
            description=(
                "List of ShopifyQL queries to sync as individual streams. "
                "Each entry produces one table in your destination. "
                "Add as many entries as needed — no code changes are required. "
                "See the 'name', 'query', and 'primary_keys' field descriptions "
                "for full details on each property. "
                "Example meltano.yml config:\n"
                "  shopifyql_queries:\n"
                "    - name: sales_over_time\n"
                "      primary_keys: [day]\n"
                "      query: >\n"
                "        FROM sales\n"
                "          SHOW orders, gross_sales, net_sales, total_sales\n"
                "          TIMESERIES day\n"
                "          SINCE 2024-01-01 UNTIL today\n"
                "          ORDER BY day ASC\n"
                "          LIMIT 1000\n"
                "    - name: inventory_snapshot\n"
                "      primary_keys: [product_id, variant_id]\n"
                "      query: >\n"
                "        FROM inventory ..."
            ),
        ),
    ).to_dict()

    def discover_streams(self) -> List[Stream]:
        """Return a list of discovered streams.

        Standard Shopify REST streams are always included. If `is_plus_account`
        is true, the UsersStream (Shopify Plus only) is added.

        Any entries in `shopifyql_queries` produce additional streams: one per
        entry, backed by ShopifyQLStream and carrying the query from config.
        """
        stream_classes = list(STREAM_TYPES)
        if self.config.get("is_plus_account"):
            stream_classes.append(UsersStream)
        streams = [cls(tap=self) for cls in stream_classes]

        for entry in self.config.get("shopifyql_queries") or []:
            streams.append(ShopifyQLStream(tap=self, query=entry))

        return streams
