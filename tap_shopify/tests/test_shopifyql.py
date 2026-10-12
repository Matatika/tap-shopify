"""Tests the ShopifyQL query streams."""

import io
import json
import re
import unittest
from contextlib import redirect_stdout

import responses

import tap_shopify.tests.utils as test_utils
from tap_shopify.client import API_VERSION

GRAPHQL_URL = f"https://mock-store.myshopify.com/admin/api/{API_VERSION}/graphql.json"

COLUMNS = [
    {"name": "day", "dataType": "DAY_TIMESTAMP"},
    {"name": "n", "dataType": "STRING"},
]

CONFIG = {
    **test_utils.basic_mock_config,
    "shopifyql_queries": [
        {
            "name": "sales",
            "query": "FROM sales SHOW n TIMESERIES day ORDER BY day ASC LIMIT 1000",
            "primary_keys": ["day"],
            "replication_key": "day",
        }
    ],
}


def table(rows):
    return {
        "data": {
            "shopifyqlQuery": {
                "parseErrors": [],
                "tableData": {"columns": COLUMNS, "rows": rows},
            }
        }
    }


def rows(count, day="2026-03-05"):
    return [{"day": day, "n": str(i)} for i in range(count)]


class TestShopifyQL(unittest.TestCase):
    """Test class for ShopifyQL query streams."""

    def setUp(self):
        responses.reset()
        self.queries = []

    def mock_api(self, *bodies):
        """Answer the schema probe, then each sync request with the next body."""
        bodies = iter(bodies)

        def callback(request):
            query = json.loads(
                re.search(
                    r"query: (\".*?\")\)", json.loads(request.body)["query"]
                ).group(1)
            )
            if "SINCE -1d" in query:
                return 200, {}, json.dumps(table([]))
            self.queries.append(query)
            return 200, {}, json.dumps(next(bodies))

        responses.add_callback(responses.POST, GRAPHQL_URL, callback=callback)

    def sync(self, state=None):
        tap = test_utils.set_up_tap_with_custom_catalog(CONFIG, ["sales"], state)
        with redirect_stdout(io.StringIO()) as out:
            tap.sync_all()
        return [json.loads(line) for line in out.getvalue().splitlines()]

    def records(self, messages):
        return [m["record"] for m in messages if m["type"] == "RECORD"]

    @responses.activate
    def test_syncs_every_page(self):
        self.mock_api(table(rows(1000)), table(rows(1)))

        messages = self.sync()

        self.assertEqual(len(self.records(messages)), 1001)
        self.assertTrue(self.queries[1].endswith("LIMIT 1000 OFFSET 1000"))

    @responses.activate
    def test_retries_a_throttled_query(self):
        throttled = {
            "errors": [{"message": "Throttled", "extensions": {"code": "THROTTLED"}}]
        }
        self.mock_api(throttled, table(rows(1)))

        messages = self.sync()

        self.assertEqual(len(self.records(messages)), 1)

    @responses.activate
    def test_syncs_incrementally_from_the_bookmark(self):
        state = {
            "bookmarks": {
                "sales": {
                    "replication_key": "day",
                    "replication_key_value": "2026-03-05T00:00:00Z",
                }
            }
        }
        self.mock_api(table(rows(1, day="2026-03-05") + rows(1, day="2026-03-06")))

        messages = self.sync(state)

        self.assertIn("SINCE 2026-03-05", self.queries[0])
        schema = next(m for m in messages if m["type"] == "SCHEMA")
        self.assertEqual(schema["key_properties"], ["day"])
        bookmark = messages[-1]["value"]["bookmarks"]["sales"]
        self.assertEqual(bookmark["replication_key_value"], "2026-03-06T00:00:00Z")
