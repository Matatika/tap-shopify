"""Tests for ShopifyQLStream's LIMIT/OFFSET pagination.

`shopifyqlQuery` has no cursor-based pagination — continuing past its
1,000-row-per-response cap means re-issuing the query with an incremented
`OFFSET`, per Shopify's own guidance (see ShopifyQLStream's docstring in
tap_shopify/streams.py). These tests cover the two pieces of that behavior
in isolation: the query-string rewrite, and the paginator's stop condition.
"""

import unittest
from unittest.mock import Mock

from tap_shopify.streams import ShopifyQLStream, _ShopifyQLPaginator


class TestPaginatedQuery(unittest.TestCase):
    """Tests for ShopifyQLStream._paginated_query."""

    def test_appends_limit_offset_when_absent(self):
        query = (
            "FROM sales SHOW total_sales TIMESERIES day SINCE 2025-01-01 "
            "UNTIL today ORDER BY day ASC"
        )

        result = ShopifyQLStream._paginated_query(query, limit=1000, offset=0)

        self.assertTrue(result.endswith("ORDER BY day ASC LIMIT 1000 OFFSET 0"))

    def test_places_limit_offset_before_trailing_visualize(self):
        query = (
            "FROM sales SHOW total_sales TIMESERIES day SINCE 2025-01-01 "
            "UNTIL today ORDER BY day ASC VISUALIZE total_sales TYPE line"
        )

        result = ShopifyQLStream._paginated_query(query, limit=1000, offset=2000)

        self.assertEqual(
            result,
            "FROM sales SHOW total_sales TIMESERIES day SINCE 2025-01-01 "
            "UNTIL today ORDER BY day ASC LIMIT 1000 OFFSET 2000 "
            "VISUALIZE total_sales TYPE line",
        )

    def test_replaces_rather_than_stacks_an_existing_limit_offset(self):
        query = (
            "FROM sales SHOW total_sales SINCE 2025-01-01 UNTIL today "
            "LIMIT 500 OFFSET 100"
        )

        result = ShopifyQLStream._paginated_query(query, limit=1000, offset=3000)

        self.assertEqual(result.count("LIMIT"), 1)
        self.assertEqual(result.count("OFFSET"), 1)
        self.assertTrue(result.endswith("LIMIT 1000 OFFSET 3000"))

    def test_replaces_existing_limit_without_offset(self):
        query = "FROM sales SHOW total_sales SINCE 2025-01-01 UNTIL today LIMIT 500"

        result = ShopifyQLStream._paginated_query(query, limit=1000, offset=0)

        self.assertEqual(result.count("LIMIT"), 1)
        self.assertTrue(result.endswith("LIMIT 1000 OFFSET 0"))


def _mock_response(rows):
    """Build a minimal fake requests.Response with a ShopifyQL-shaped body."""
    response = Mock()
    response.json.return_value = {
        "data": {"shopifyqlQuery": {"tableData": {"rows": rows}}}
    }
    return response


class TestShopifyQLPaginator(unittest.TestCase):
    """Tests for _ShopifyQLPaginator's continue/stop decisions."""

    def test_continues_when_page_is_full(self):
        paginator = _ShopifyQLPaginator(
            start_value=0, page_size=1000, max_pages=50, stream_name="test_stream"
        )

        self.assertTrue(paginator.has_more(_mock_response(rows=["row"] * 1000)))

    def test_stops_when_page_is_partial(self):
        paginator = _ShopifyQLPaginator(
            start_value=1000, page_size=1000, max_pages=50, stream_name="test_stream"
        )

        self.assertFalse(paginator.has_more(_mock_response(rows=["row"] * 250)))

    def test_stops_when_page_is_empty(self):
        paginator = _ShopifyQLPaginator(
            start_value=2000, page_size=1000, max_pages=50, stream_name="test_stream"
        )

        self.assertFalse(paginator.has_more(_mock_response(rows=[])))

    def test_safety_cap_stops_pagination_even_on_a_full_page(self):
        paginator = _ShopifyQLPaginator(
            start_value=49000, page_size=1000, max_pages=50, stream_name="test_stream"
        )
        # advance() increments the page count before has_more() sees it, so
        # simulate 49 prior full pages the same way: via advance(), not by
        # calling has_more() directly (which would never see the increment).
        for _ in range(49):
            paginator.advance(_mock_response(rows=["row"] * 1000))
        self.assertFalse(paginator.finished)

        # The 50th page also comes back full — without the safety cap this
        # would keep going; with it, pagination must stop regardless.
        paginator.advance(_mock_response(rows=["row"] * 1000))

        self.assertTrue(paginator.finished)

    def test_advance_increments_offset_by_page_size(self):
        paginator = _ShopifyQLPaginator(
            start_value=0, page_size=1000, max_pages=50, stream_name="test_stream"
        )

        paginator.advance(_mock_response(rows=["row"] * 1000))

        self.assertEqual(paginator.current_value, 1000)
        self.assertFalse(paginator.finished)

    def test_advance_marks_finished_on_partial_page(self):
        paginator = _ShopifyQLPaginator(
            start_value=1000, page_size=1000, max_pages=50, stream_name="test_stream"
        )

        paginator.advance(_mock_response(rows=["row"] * 10))

        self.assertTrue(paginator.finished)


if __name__ == "__main__":
    unittest.main()
