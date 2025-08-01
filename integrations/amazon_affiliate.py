"""
Amazon Associates (affiliate) integration for Nova Agent.

This module helps generate affiliate links to Amazon products using
the Amazon Associates program. When Nova includes product links in
video descriptions or landing pages, appending the associate tag
ensures referral commissions are tracked. This simple helper
constructs a link containing the associate tag for a given product
URL or ASIN.

Environment variables expected:

    AMAZON_ASSOCIATE_TAG:
        Your Amazon Associates tracking ID (also known as the tag).
        The tag should look like ``myaffiliate-20``. Without this
        environment variable the helper will raise a RuntimeError.

Usage example::

    from integrations.amazon_affiliate import generate_affiliate_link
    url = generate_affiliate_link("https://www.amazon.com/dp/B08CFSZLQ4")
    # url will be something like
    # "https://www.amazon.com/dp/B08CFSZLQ4?tag=myaffiliate-20"

Note: This helper does not validate product IDs or perform any API
calls. It simply appends the tag query parameter to the URL. For
markets outside the US, adjust the domain accordingly and provide
country‑specific tags via additional functions if needed.
"""

from __future__ import annotations

import os
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse


def generate_affiliate_link(product_url: str) -> str:
    """Append the Amazon Associates tag to a product URL.

    Args:
        product_url: The original Amazon product URL or deep link.

    Returns:
        A new URL containing the affiliate tag.

    Raises:
        RuntimeError: If AMAZON_ASSOCIATE_TAG is not set.
        ValueError: If the provided URL is not an Amazon URL.
    """
    tag = os.getenv("AMAZON_ASSOCIATE_TAG")
    if not tag:
        raise RuntimeError(
            "AMAZON_ASSOCIATE_TAG environment variable must be set to generate affiliate links"
        )
    parsed = urlparse(product_url)
    if "amazon." not in parsed.netloc.lower():
        raise ValueError("The provided URL does not appear to be an Amazon link")
    # Preserve existing query parameters and add/replace the tag
    query_params = dict(parse_qsl(parsed.query))
    query_params["tag"] = tag
    new_query = urlencode(query_params)
    new_url = urlunparse(
        (parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment)
    )
    return new_url