"""
Beacons integration for Nova Agent.

Beacons (https://beacons.ai) is a link-in-bio platform used to
aggregate multiple calls-to-action (CTAs) and social links into a
single page.  This module provides simple helpers to generate profile
links and to update the list of links displayed on a Beacons page.  At
present, Beacons does not offer a public, documented API for
updating pages; therefore the ``update_links`` function is a stub
implementation that returns the payload it would send to such an API.
In a production deployment, operators can replace this stub with
custom code or use an automation tool (e.g. Beacons Zapier
integration) to update the page.

Environment variables expected:

    BEACONS_API_KEY (optional):
        API key to authenticate with the Beacons service if one is
        provided in the future.  Currently unused.

Usage example::

    from integrations.beacons import generate_profile_link, update_links
    url = generate_profile_link("myusername")
    # url -> "https://beacons.ai/myusername"
    new_links = [
        {"title": "YouTube", "url": "https://youtube.com/..."},
        {"title": "Shop", "url": "https://myshop.com"},
    ]
    result = update_links("myusername", new_links)
"""

from __future__ import annotations

import os
from typing import Any, Dict, List


def generate_profile_link(username: str) -> str:
    """Return the Beacons profile URL for a given username."""
    # Basic sanitation: strip leading @ if provided
    if username.startswith("@"):  # remove leading @ symbol
        username = username[1:]
    return f"https://beacons.ai/{username}"


def update_links(username: str, links: List[Dict[str, str]]) -> Dict[str, Any]:
    """Stub function to update the list of links on a Beacons page.

    Beacons does not currently provide a public REST API for updating
    link lists programmatically.  This function returns the payload that
    would be sent to such an API, allowing unit tests to verify
    behaviour.  Operators may replace this stub with custom logic or
    automation to perform the update via browser automation or third
    party integrations.

    Args:
        username: Beacons username of the page owner.
        links: A list of dictionaries with ``title`` and ``url`` keys.

    Returns:
        A dictionary summarising the intended update payload.
    """
    api_key = os.getenv("BEACONS_API_KEY")  # Unused at present
    # Validate links structure
    for link in links:
        if not isinstance(link, dict) or "title" not in link or "url" not in link:
            raise ValueError("Each link must be a dict with 'title' and 'url'")
    payload = {
        "username": username.lstrip("@"),
        "links": links,
        "api_key_used": bool(api_key),
    }
    # In a real implementation, you would perform an HTTP request here
    # to the Beacons API endpoint using the api_key for authentication.
    return payload
