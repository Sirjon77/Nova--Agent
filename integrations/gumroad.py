"""
Gumroad integration helpers for Nova Agent.

This module provides simple wrappers around the Gumroad API to support
basic e‑commerce operations. Nova can use these helpers to
generate affiliate links for Gumroad products or to create products
programmatically.  These functions intentionally cover only the
minimum features needed to integrate Gumroad with the content
automation pipeline.  Advanced storefront management should be
implemented outside of Nova and integrated via custom workflows.

Environment variables expected:

    GUMROAD_AFFILIATE_ID (optional):
        Your Gumroad affiliate ID.  When provided, generated product
        links will include this identifier for referral tracking.

    GUMROAD_ACCESS_TOKEN (optional):
        A personal access token to authenticate against the Gumroad API.
        Required for operations that create or update products.  See
        https://gumroad.com/developers to obtain a token.

Usage example::

    from integrations.gumroad import generate_product_link, create_product

    # Generate a link for a product slug with affiliate tracking
    url = generate_product_link("amazing-course")
    # "https://gum.co/amazing-course?affiliate_id=your_affiliate_id"

    # Create a new product via the API
    product = create_product(
        name="AI Course",
        description="Learn the basics of AI.",
        price_cents=9900,
        max_purchase_count=0,
    )

Notes:
    - Gumroad's API uses the slug form of a product (e.g., `amazing-course`) to
      construct product URLs.  Use the `generate_product_link` helper when you
      already have a slug and just need a link.
    - For product creation, only a subset of fields are exposed here.  See
      https://gumroad.com/developers/api#products for the full API and
      adjust or extend this helper as needed.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import requests


def generate_product_link(product_slug: str, *, include_affiliate: bool = True) -> str:
    """Construct a Gumroad product link.

    Args:
        product_slug: The Gumroad product slug (e.g., ``"amazing-course"``).
        include_affiliate: Whether to append the affiliate ID query
            parameter when ``GUMROAD_AFFILIATE_ID`` is set.  Defaults
            to True.

    Returns:
        A URL pointing to the product's Gumroad landing page.  If
        ``include_affiliate`` is True and ``GUMROAD_AFFILIATE_ID`` is
        configured, the link will include ``?affiliate_id=<id>``.
    """
    base_url = f"https://gum.co/{product_slug}"
    affiliate_id = os.getenv("GUMROAD_AFFILIATE_ID")
    if include_affiliate and affiliate_id:
        return f"{base_url}?affiliate_id={affiliate_id}"
    return base_url


def _gumroad_api_request(endpoint: str, method: str = "GET", *, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Internal helper to perform authenticated requests to Gumroad's API.

    Args:
        endpoint: API path such as ``"products"`` or ``"products/{id}"``.
        method: HTTP method to use ("GET", "POST", etc.).
        data: JSON payload for POST/PUT requests.

    Returns:
        Parsed JSON response from the Gumroad API.

    Raises:
        RuntimeError: If authentication fails or the API returns an
            unsuccessful status code.
    """
    token = os.getenv("GUMROAD_ACCESS_TOKEN")
    if not token:
        raise RuntimeError(
            "GUMROAD_ACCESS_TOKEN environment variable must be set to call the Gumroad API"
        )
    url = f"https://api.gumroad.com/v2/{endpoint}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.request(method, url, json=data, headers=headers, timeout=15)
    try:
        resp_json = response.json()
    except Exception:
        resp_json = {}
    if not response.ok or (resp_json.get("success") is False):
        raise RuntimeError(
            f"Gumroad API request failed ({response.status_code}): {resp_json or response.text}"
        )
    return resp_json  # type: ignore[return-value]


def create_product(
    *,
    name: str,
    description: str,
    price_cents: int,
    max_purchase_count: int = 0,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Create a new digital product on Gumroad.

    Args:
        name: Name of the product (e.g., ``"AI Course"``).
        description: A plain‑text description of the product.
        price_cents: Price in cents (e.g., 9900 for $99.00).
        max_purchase_count: Maximum number of purchases allowed.  Zero
            means unlimited.  Defaults to 0.
        **kwargs: Additional fields accepted by the Gumroad API such as
            ``custom_permalink``, ``url``, etc.

    Returns:
        The response from Gumroad's API containing details of the
        created product.

    Raises:
        RuntimeError: If the API returns an error or authentication
            credentials are missing.
    """
    payload: Dict[str, Any] = {
        "product": {
            "name": name,
            "description": description,
            "price": price_cents,
            "max_purchase_count": max_purchase_count,
        }
    }
    # Merge additional fields into the payload
    if kwargs:
        payload["product"].update(kwargs)
    return _gumroad_api_request("products", method="POST", data=payload)
