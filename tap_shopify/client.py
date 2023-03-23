"""REST client handling, including tap_shopifyStream base class."""

from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import parse_qsl, urlsplit

import requests
from singer_sdk.streams import RESTStream

from tap_shopify.auth import tap_shopifyAuthenticator

SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")


class tap_shopifyStream(RESTStream):
    """tap_shopify stream class."""

    @property
    def url_base(self) -> str:
        """Return the API URL root, configurable via tap settings."""
        url_base = self.config.get(
            "admin_url"
        ) or "https://%s.myshopify.com/admin" % self.config.get("store")
        return url_base

    records_jsonpath = "$[*]"  # Or override `parse_response`.
    next_page_token_jsonpath = "$.next_page"  # Or override `get_next_page_token`.
    last_id = None

    @property
    def authenticator(self):
        """Return a new authenticator object."""
        return tap_shopifyAuthenticator(
            self,
            key="X-Shopify-Access-Token",
            value=str(self.config["access_token"]),
            location="header",
        )

    @property
    def http_headers(self) -> dict:
        """Return the http headers needed."""
        headers = {}
        if "user_agent" in self.config:
            headers["User-Agent"] = self.config.get("user_agent")
        return headers

    def get_next_page_token(
        self, response: requests.Response, previous_token: Optional[Any]
    ) -> Optional[Any]:
        """Return a token for identifying next page or None if no more pages."""
        next_link = response.links.get("next")
        if not next_link or not response.json():
            self.last_id = None
            return None

        return next_link["url"]

    def get_url_params(
        self, context: Optional[dict], next_page_token: Optional[Any]
    ) -> Dict[str, Any]:
        """Return a dictionary of values to be used in URL parameterization."""
        params: dict = {}

        if next_page_token:
            return dict(parse_qsl(urlsplit(next_page_token).query))

        context_state = self.get_context_state(context)
        last_updated = context_state.get("replication_key_value")

        start_date = self.config.get("start_date")

        if last_updated:
            params["updated_at_min"] = last_updated
            return params
        elif start_date:
            params["created_at_min"] = start_date
        return params

    def post_process(self, row: dict, context: Optional[dict] = None):
        """Deduplicate rows by id or updated_at."""
        current_row_id = row.get("id")

        updated_at = row.get("updated_at")

        if (current_row_id and current_row_id == self.last_id) or (
            updated_at == self.get_starting_replication_key_value(context)
        ):
            return None

        self.last_id = current_row_id
        return row
