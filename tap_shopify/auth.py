"""tap_shopify Authentication."""

from singer_sdk.authenticators import APIKeyAuthenticator, SingletonMeta


# The SingletonMeta metaclass makes the streams reuse the same authenticator instance.
class tap_shopifyAuthenticator(APIKeyAuthenticator, metaclass=SingletonMeta):
    """Authenticator class for tap_shopify."""

    @classmethod
    def create_for_stream(cls, stream) -> "tap_shopifyAuthenticator":
        """Create Authtenticator for supplied Stream."""
        return cls(
            stream=stream,
            key="X-Shopify-Access-Token",
            value=stream.config["access_token"],
            location="header",
        )
