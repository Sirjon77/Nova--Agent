"""
HubSpot CRM integration for Nova Agent.

This module provides minimal helpers to create contacts within HubSpot.
HubSpot offers a comprehensive REST API for interacting with CRM
objects (see https://developers.hubspot.com/docs/api/crm/contacts).  The
function defined here focuses on creating a simple contact record
containing an email address and basic name fields.  Additional
properties can be supplied via keyword arguments.

Environment variables expected:

    HUBSPOT_API_KEY:
        A private app API key for HubSpot CRM.  Required for all
        requests.  See https://knowledge.hubspot.com/integrations/how-do-i-get-my-hubspot-api-key.

Usage example::

    from integrations.hubspot import create_contact
    contact = create_contact(
        email="jane@example.com",
        first_name="Jane",
        last_name="Doe",
        company="Example Corp"
    )
    # contact -> API response from HubSpot
"""

from __future__ import annotations

import os
from typing import Any, Dict, Union

import requests


class HubSpotError(RuntimeError):
    """Raised when a HubSpot API call fails."""


def _hubspot_request(endpoint: str, method: str = "POST", *, data: Dict[str, Any]) -> Dict[str, Any]:
    api_key = os.getenv("HUBSPOT_API_KEY")
    if not api_key:
        raise HubSpotError("HUBSPOT_API_KEY must be set to use the HubSpot API")
    url = f"https://api.hubapi.com{endpoint}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    response = requests.request(method, url, json=data, headers=headers, timeout=15)
    try:
        resp_json = response.json()
    except Exception:
        resp_json = {}
    if not response.ok or "status" in resp_json and resp_json.get("status") == "error":
        raise HubSpotError(f"HubSpot API error ({response.status_code}): {resp_json or response.text}")
    return resp_json  # type: ignore[return-value]


def create_contact(
    *,
    email: str,
    first_name: Union[str, None] = None,
    last_name: Union[str, None] = None,
    **properties: Any,
) -> Dict[str, Any]:
    """Create a contact in HubSpot CRM.

    Args:
        email: The contact's email address (required by HubSpot).
        first_name: Optional first name.
        last_name: Optional last name.
        **properties: Additional HubSpot properties such as company,
            job title, phone number, etc.  Property names should
            correspond to HubSpot contact properties.

    Returns:
        The created contact record as returned by the HubSpot API.

    Raises:
        HubSpotError: If the API call fails or credentials are missing.
    """
    data = {
        "properties": {
            "email": email,
        }
    }
    if first_name:
        data["properties"]["firstname"] = first_name
    if last_name:
        data["properties"]["lastname"] = last_name
    # Merge any additional properties
    if properties:
        # HubSpot uses lowercase property names; keep as provided
        data["properties"].update(properties)
    # Perform API call
    return _hubspot_request("/crm/v3/objects/contacts", method="POST", data=data)
