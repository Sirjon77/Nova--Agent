"""
TubeBuddy/YouTube Data API integration for Nova Agent.

TubeBuddy is a popular browser extension and platform for YouTube
creators offering keyword research, SEO analysis, A/B testing and
automation tools【395692199587272†L90-L102】. While TubeBuddy itself does not
expose a public API, the YouTube Data API can be used to perform
similar keyword and trend analyses. This module provides helper
functions for searching keywords and fetching trending videos via
Google's official API. Operators can use these functions in place
of or alongside the existing vidIQ integration.

Environment variables expected:

    GOOGLE_API_KEY or TUBEBUDDY_API_KEY:
        API key for the YouTube Data API. Either variable may be
        defined; ``GOOGLE_API_KEY`` takes precedence. You can obtain
        an API key from the Google Cloud Console.

    DEFAULT_REGION (optional):
        Two‑letter country code (e.g. "US") used as the default
        region for trending requests. Defaults to "US" if not set.

Example usage::

    from integrations.tubebuddy import search_keywords, get_trending_videos
    keywords = search_keywords("cat videos", max_results=5)
    trending = get_trending_videos(region="CA", max_results=5)

These functions perform synchronous HTTP requests and may be slow.
Consider running them in an executor when called from an async
context.
"""

from __future__ import annotations

import os
from typing import List, Dict, Any, Optional, Union

import requests


class TubeBuddyError(Exception):
    """Raised when a YouTube Data API call fails."""


def _get_api_key() -> str:
    """Return the API key to use for YouTube Data API calls.

    Prefers the ``GOOGLE_API_KEY`` environment variable but falls
    back to ``TUBEBUDDY_API_KEY`` for compatibility with the
    TubeBuddy nomenclature.

    Raises RuntimeError if neither is defined.
    """
    key = os.getenv("GOOGLE_API_KEY") or os.getenv("TUBEBUDDY_API_KEY")
    if not key:
        raise RuntimeError(
            "You must set either GOOGLE_API_KEY or TUBEBUDDY_API_KEY to use the TubeBuddy integration."
        )
    return key


def search_keywords(
    query: str,
    max_results: int = 10,
    category: Union[str, None] = None,
) -> List[str]:
    """Search YouTube for a given query and return a list of related keywords.

    This helper uses the YouTube Search API to find videos related to
    the given query. It then extracts tags from the video snippets
    and returns a deduplicated list of keywords. The results are
    limited to ``max_results`` videos.

    Args:
        query: Search term.
        max_results: Maximum number of videos to inspect.

    Returns:
        A list of keywords/tags relevant to the search query.

    Raises:
        TubeBuddyError: If the API request fails or returns an
            unexpected structure.
    """
    api_key = _get_api_key()
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "maxResults": max_results,
        "type": "video",
        "key": api_key,
    }
    resp = requests.get(url, params=params, timeout=20)
    if resp.status_code >= 400:
        raise TubeBuddyError(
            f"YouTube Search API returned {resp.status_code}: {resp.text}"
        )
    data = resp.json()
    items = data.get("items", [])
    keywords: List[str] = []
    for item in items:
        snippet = item.get("snippet", {})
        # Title and description often contain valuable keywords
        title = snippet.get("title", "")
        description = snippet.get("description", "")
        combined = f"{title} {description}"
        # Split on whitespace and punctuation to get simple tokens
        for token in combined.split():
            token_clean = token.strip().lower().strip("\"',.?!#()")
            # Exclude the query itself and very short tokens
            if token_clean and token_clean != query.lower() and len(token_clean) > 3:
                keywords.append(token_clean)
    # Deduplicate while preserving order
    seen = set()
    deduped: List[str] = []
    for kw in keywords:
        if kw not in seen:
            seen.add(kw)
            deduped.append(kw)
    return deduped[:max_results]


def get_trending_videos(
    *,
    region: Optional[str] = None,
    category: Union[str, None] = None,
    max_results: int = 10,
) -> List[Dict[str, Any]]:
    """Fetch the current trending videos for a given region via the YouTube API.

    Uses the ``videos`` endpoint with ``chart=mostPopular``. You may
    specify a region code (ISO 3166‑1 alpha‑2) and/or a category ID
    (see https://developers.google.com/youtube/v3/docs/videoCategories/list).

    Args:
        region: Two‑letter region code (e.g. "US", "GB"). Defaults to
            ``DEFAULT_REGION`` environment variable or "US".
        category: Optional YouTube category ID as a string. If
            provided, results will be filtered by category.
        max_results: Number of videos to return (max 50).

    Returns:
        A list of dictionaries containing video metadata (id, title,
        description, channel title).

    Raises:
        TubeBuddyError: If the API call fails or returns unexpected
            data.
    """
    api_key = _get_api_key()
    region_code = region or os.getenv("DEFAULT_REGION", "US")
    params = {
        "part": "snippet,contentDetails,statistics",
        "chart": "mostPopular",
        "regionCode": region_code,
        "maxResults": max_results,
        "key": api_key,
    }
    if category:
        params["videoCategoryId"] = category
    url = "https://www.googleapis.com/youtube/v3/videos"
    resp = requests.get(url, params=params, timeout=20)
    if resp.status_code >= 400:
        raise TubeBuddyError(
            f"YouTube Videos API returned {resp.status_code}: {resp.text}"
        )
    data = resp.json()
    items = data.get("items", [])
    results: List[Dict[str, Any]] = []
    for item in items:
        snippet = item.get("snippet", {})
        vid_info = {
            "id": item.get("id"),
            "title": snippet.get("title"),
            "description": snippet.get("description"),
            "channelTitle": snippet.get("channelTitle"),
        }
        results.append(vid_info)
    return results