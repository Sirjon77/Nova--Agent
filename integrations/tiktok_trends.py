"""
TikTok trending topics integration for Nova Agent.

TikTok does not provide an official public API for retrieving
trending hashtags or topics. This module offers a best‑effort
approach to fetch trending terms using a configurable endpoint. If
no endpoint is configured via the ``TIKTOK_TREND_ENDPOINT``
environment variable, the function returns an empty list. You may
point ``TIKTOK_TREND_ENDPOINT`` at an unofficial API or a proxy
service that scrapes TikTok's trending page and returns JSON.

The return format is a list of dictionaries with at minimum the
keys ``term`` (the hashtag or topic name) and ``views`` (an integer
or string representing the popularity). Additional keys from the
underlying API are passed through.
"""

from __future__ import annotations

import os
import requests
from typing import Any, Dict, List


def get_trending_topics(*, region: str = "us", limit: int = 10) -> List[Dict[str, Any]]:
    """Fetch trending TikTok topics or hashtags.

    Args:
        region: Optional region or market code to filter trends. The
            underlying API must support this parameter; otherwise it
            will be ignored. Default is ``"us"``.
        limit: Maximum number of trending terms to return. The
            actual number returned may be less depending on API
            availability.

    Returns:
        A list of dictionaries each representing a trending topic.
        Each dictionary will at minimum contain a ``term`` key and
        optionally a ``views`` key.

    Note:
        This function will quietly return an empty list if no
        endpoint is configured or if the request fails. You can
        inspect logs or exceptions for debugging but the calling
        code should handle empty results gracefully.
    """
    endpoint = os.getenv("TIKTOK_TREND_ENDPOINT")
    if not endpoint:
        # No endpoint configured; return nothing.
        return []

    params = {
        "region": region,
        "limit": limit,
    }
    try:
        resp = requests.get(endpoint, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        # Expecting the API to return a list of items; each item
        # should at least have a name/term. Map fields accordingly.
        trends: List[Dict[str, Any]] = []
        if isinstance(data, list):
            for item in data[:limit]:
                # Attempt to extract term and views metrics.
                term = item.get("term") or item.get("name") or item.get("hashtag")
                views = item.get("views") or item.get("count")
                if term:
                    trend: Dict[str, Any] = {"term": term}
                    if views:
                        trend["views"] = views
                    # Include any additional keys to be transparent.
                    for k, v in item.items():
                        if k not in trend:
                            trend[k] = v
                    trends.append(trend)
        return trends
    except Exception:
        # On error, return empty list. In a real implementation you
        # might log the exception.
        return []