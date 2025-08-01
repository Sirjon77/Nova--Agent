"""
ConvertKit integration helpers for Nova Agent.

This module wraps common ConvertKit API calls so that Nova can
subscribe users to mailing lists, tag them based on interests, and
integrate with funnel sequences.  The functions here intentionally
cover a minimal set of features needed to link Nova's content to
email marketing funnels.  See https://developers.convertkit.com/ for
the full API documentation.

Environment variables expected:

    CONVERTKIT_API_KEY:
        Your ConvertKit API key.  Required for all requests.

    CONVERTKIT_API_SECRET (optional):
        Secret API key for certain endpoints that require additional
        authentication.  Not needed for simple list subscribe.

    CONVERTKIT_FORM_ID (optional):
        Default form ID for subscription if not provided explicitly.

Usage example::

    from integrations.convertkit import subscribe_user

    # Subscribe an email address to the default form with a tag
    result = subscribe_user(
        email="user@example.com",
        first_name="Alice",
        tags=["fitness", "latam"]
    )

    # Subscribe to a specific form and broadcast via tags
    result2 = subscribe_user(
        email="bob@example.com",
        form_id="123456",
        tags=["ai-course"]
    )

Notes:
    - If you wish to add tags to an existing subscriber without
      subscribing them to a form again, use ``add_tags_to_subscriber``.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Iterable, Optional

import requests


class ConvertKitError(RuntimeError):
    """Raised when a ConvertKit API call fails."""


def _convertkit_request(
    endpoint: str,
    method: str = "POST",
    *,
    json_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Internal helper to call the ConvertKit API with the proper credentials.

    Args:
        endpoint: API path relative to ``https://api.convertkit.com/v3/``.
        method: HTTP method.  Defaults to ``POST`` as most endpoints
            require POST.
        json_data: JSON body to send with the request.

    Returns:
        Parsed JSON response.

    Raises:
        ConvertKitError: If authentication info is missing or the
            response indicates an error.
    """
    api_key = os.getenv("CONVERTKIT_API_KEY")
    if not api_key:
        raise ConvertKitError("CONVERTKIT_API_KEY must be set to use the ConvertKit API")
    url = f"https://api.convertkit.com/v3/{endpoint}"
    payload = json_data or {}
    # Always include the API key in the payload per ConvertKit docs
    payload.setdefault("api_key", api_key)
    response = requests.request(method, url, json=payload, timeout=15)
    try:
        data = response.json()
    except Exception:
        raise ConvertKitError(f"ConvertKit API returned invalid JSON: {response.text}")
    if response.status_code >= 400 or data.get("error"):
        raise ConvertKitError(f"ConvertKit API error ({response.status_code}): {data}")
    return data  # type: ignore[return-value]


def subscribe_user(
    *,
    email: str,
    first_name: Optional[str] = None,
    form_id: Optional[str] = None,
    tags: Optional[Iterable[str]] = None,
) -> Dict[str, Any]:
    """Subscribe a user to a ConvertKit form and optionally apply tags.

    Args:
        email: Subscriber's email address.
        first_name: Optional first name for personalization.
        form_id: ID of the form to subscribe the user to.  If None,
            uses the ``CONVERTKIT_FORM_ID`` environment variable.
        tags: Iterable of tag names to apply to the subscriber after
            subscription.  Tags help segment subscribers based on
            interests or campaigns.

    Returns:
        JSON response from ConvertKit detailing the subscriber record.

    Raises:
        ConvertKitError: On missing credentials or API error.
    """
    target_form_id = form_id or os.getenv("CONVERTKIT_FORM_ID")
    if not target_form_id:
        raise ConvertKitError(
            "Form ID must be provided either as an argument or via CONVERTKIT_FORM_ID"
        )
    payload: Dict[str, Any] = {"email": email}
    if first_name:
        payload["first_name"] = first_name
    if tags:
        # ConvertKit expects tags as a list of integers (tag IDs) or names; here we accept names and pass through
        payload["tags"] = list(tags)
    # POST to subscribe endpoint
    endpoint = f"forms/{target_form_id}/subscribe"
    return _convertkit_request(endpoint, method="POST", json_data=payload)


def add_tags_to_subscriber(*, subscriber_id: str, tags: Iterable[str]) -> Dict[str, Any]:
    """Apply one or more tags to an existing subscriber.

    Args:
        subscriber_id: The unique ID of the subscriber in ConvertKit.
        tags: Iterable of tag names to apply.

    Returns:
        JSON response with updated subscriber info.

    Raises:
        ConvertKitError: On API errors or missing credentials.
    """
    payload = {"tags": list(tags)}
    endpoint = f"subscribers/{subscriber_id}/tags"
    return _convertkit_request(endpoint, method="POST", json_data=payload)
