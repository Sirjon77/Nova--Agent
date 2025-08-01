"""
vidIQ API integration for Nova Agent.

vidIQ provides insights and analytics for YouTube channels,
including trending keywords and search volume estimates. This
module exposes a simple function to fetch trending keywords from
vidIQ's API, intended for use in the trend scanner or content
ideation processes. To use this integration, you must supply a
vidIQ API key via the environment variable `VIDIQ_API_KEY`.

At the time of writing there is no official public documentation
for vidIQ's API, so this implementation uses a hypothetical
endpoint based on community resources. You should verify the
endpoint and response structure against your vidIQ plan.
"""

import os
import requests
from typing import List, Tuple

VIDIQ_API_KEY = os.getenv("VIDIQ_API_KEY")

class VidiqError(Exception):
    """Raised when the vidIQ API returns an error or invalid data."""


def get_trending_keywords(max_items: int = 10) -> List[Tuple[str, float]]:
    """Retrieve the top trending search keywords from vidIQ.

    Args:
        max_items: Maximum number of keywords to return.

    Returns:
        A list of tuples `(keyword, score)` where `score` is a
        floating‑point value representing relative interest. The
        semantics of the score depend on vidIQ's API.

    Raises:
        VidiqError: If credentials are missing or an API error occurs.
    """
    if not VIDIQ_API_KEY:
        raise VidiqError("VIDIQ_API_KEY is not set in environment variables")
    url = "https://vidiq.com/api/trending"
    headers = {"Authorization": f"Bearer {VIDIQ_API_KEY}"}
    resp = requests.get(url, headers=headers, timeout=10)
    if resp.status_code >= 400:
        raise VidiqError(f"vidIQ API error {resp.status_code}: {resp.text}")
    try:
        data = resp.json()
    except ValueError:
        raise VidiqError("Invalid JSON response from vidIQ API")
    items = data.get("trending", [])
    results: List[Tuple[str, float]] = []
    for item in items:
        term = item.get("keyword")
        score = float(item.get("score", 0.0))
        if term:
            results.append((term, score))
        if len(results) >= max_items:
            break
    return results