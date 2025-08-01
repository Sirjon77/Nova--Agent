"""
Metricool API integration for Nova Agent.

Metricool offers analytics and management tools for social media
channels, providing aggregated metrics across platforms like
YouTube, TikTok, Instagram and Facebook. This module provides a
rudimentary wrapper around Metricool's HTTP API to retrieve
performance metrics that the Nova Agent can use to score channels
or trigger actions.

The Metricool API requires authentication via an API token. You must
set the following environment variables for this integration to
function:

    METRICOOL_API_TOKEN
    METRICOOL_ACCOUNT_ID

Consult the official Metricool documentation to adjust endpoints or
parameters as needed. The current implementation provides a
`get_metrics` function that fetches basic insights for a channel.
"""

import os
import requests
from typing import Dict, Any, Optional

METRICOOL_API_TOKEN = os.getenv("METRICOOL_API_TOKEN")
METRICOOL_ACCOUNT_ID = os.getenv("METRICOOL_ACCOUNT_ID")

class MetricoolError(Exception):
    """Raised when the Metricool API returns an error."""


def get_metrics(profile_id: str) -> Dict[str, Any]:
    """Fetch summary metrics for a given social profile.

    Args:
        profile_id: The Metricool profile identifier for which to
            retrieve metrics. This could correspond to a YouTube
            channel ID, TikTok handle, etc., depending on how your
            Metricool account is configured.

    Returns:
        A dictionary containing metrics such as followers, views,
        interactions, and other platform‑specific analytics. The
        structure of the returned data matches Metricool's API
        response.

    Raises:
        ValueError: If the API credentials are not configured.
        MetricoolError: If the API returns a non‑success status.
    """
    if not METRICOOL_API_TOKEN or not METRICOOL_ACCOUNT_ID:
        raise ValueError(
            "METRICOOL_API_TOKEN and METRICOOL_ACCOUNT_ID environment variables must be set"
        )
    # Construct the request URL. Adjust the endpoint path according to
    # Metricool's API spec. Here we assume a hypothetical endpoint
    # "https://api.metricool.com/v1/accounts/{account_id}/profiles/{profile_id}/metrics".
    url = (
        f"https://api.metricool.com/v1/accounts/{METRICOOL_ACCOUNT_ID}/"
        f"profiles/{profile_id}/metrics"
    )
    headers = {
        "Authorization": f"Bearer {METRICOOL_API_TOKEN}",
        "Accept": "application/json",
    }
    response = requests.get(url, headers=headers)
    if response.status_code >= 400:
        raise MetricoolError(
            f"Metricool API error {response.status_code}: {response.text}"
        )
    try:
        return response.json()  # type: ignore[no-any-return]
    except ValueError:
        raise MetricoolError("Invalid JSON response from Metricool API")


def get_overview() -> Optional[Dict[str, Any]]:
    """Fetch an overview of account‑level analytics from Metricool.

    Returns:
        A dictionary with high‑level metrics aggregated across all
        profiles, or None if credentials are missing.
    """
    if not METRICOOL_API_TOKEN or not METRICOOL_ACCOUNT_ID:
        return None
    url = f"https://api.metricool.com/v1/accounts/{METRICOOL_ACCOUNT_ID}/overview"
    headers = {
        "Authorization": f"Bearer {METRICOOL_API_TOKEN}",
        "Accept": "application/json",
    }
    response = requests.get(url, headers=headers)
    if response.status_code >= 400:
        return None
    try:
        return response.json()
    except ValueError:
        return None