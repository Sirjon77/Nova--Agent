"""
Global Web Index (GWI) integration for Nova Agent.

This module provides helper functions to fetch trending topics from
GWI or another audience‑insights service. Because GWI does not
provide a public unauthenticated API, this implementation relies on
an environment variable specifying a custom endpoint and an API key.

To enable GWI trend scanning set the following environment
variables:

``GWI_TREND_ENDPOINT`` – The base URL for the trend API (e.g.
``https://api.example.com/gwi/trends``).  The endpoint should
return JSON data when queried with region and limit parameters.

``GWI_API_KEY`` – A token used for authentication.  It will be
included as a Bearer token in the ``Authorization`` header.

The ``get_trending_topics`` function accepts a region code and
returns a list of dictionaries.  Each dictionary will include at
minimum a ``term`` key and an ``interest`` score.  Additional
fields from the upstream API are passed through unchanged.  If no
endpoint or key is configured, or if a request fails, the function
returns an empty list.  Calling code should handle an empty list
gracefully.
"""

from __future__ import annotations

import os
import requests
from typing import List, Dict, Any


def get_trending_topics(*, region: str = "us", limit: int = 10) -> List[Dict[str, Any]]:
    """Fetch trending topics from Global Web Index.

    Args:
        region: A market or audience segment code (e.g. ``"us"``) used
            to filter trends.  Passed through to the endpoint as a
            query parameter.  Defaults to ``"us"``.
        limit: Maximum number of items to return.  The upstream API
            may ignore this hint.  Defaults to ``10``.

    Returns:
        A list of dictionaries, each containing at minimum ``term`` and
        ``interest`` keys.  Additional fields from the API are
        preserved.  If the endpoint or API key is not set or the
        request fails, an empty list is returned.
    """
    endpoint = os.getenv("GWI_TREND_ENDPOINT")
    api_key = os.getenv("GWI_API_KEY")
    # If no endpoint or API key is provided, return nothing
    if not endpoint or not api_key:
        return []
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }
    params = {
        "region": region,
        "limit": limit,
    }
    try:
        resp = requests.get(endpoint, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        # On error, return empty list to avoid breaking the trend scan
        return []
    # The expected response is a list of objects; each should have
    # either a 'term' or 'keyword' field and optionally an
    # 'interest' metric.  Map these into a uniform structure.
    trends: List[Dict[str, Any]] = []
    if isinstance(data, list):
        for item in data[:limit]:
            term = item.get("term") or item.get("keyword") or item.get("name")
            interest = item.get("interest") or item.get("score") or item.get("views")
            if term:
                trend: Dict[str, Any] = {"term": term}
                if interest is not None:
                    # Cast interest to float if possible
                    try:
                        trend["interest"] = float(interest)
                    except Exception:
                        trend["interest"] = interest
                # Include additional fields verbatim
                for k, v in item.items():
                    if k not in trend:
                        trend[k] = v
                trends.append(trend)
    return trends