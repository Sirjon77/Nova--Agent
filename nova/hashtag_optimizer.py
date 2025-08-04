"""Hashtag Optimisation Engine.

This module provides a simple interface for generating and ranking
hashtags tailored to specific topics, platforms and regions.  The
``HashtagOptimizer`` class uses heuristics such as popularity,
relevance and competition to suggest hashtags.  Although it
currently relies on static lists, future implementations could
integrate with social media APIs or third-party services (e.g.,
Metricool) to fetch real-time hashtag analytics.

The goal of the optimiser is to improve content discoverability
across multiple platforms without diluting the niche focus.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Tuple, Iterable, Any, Union


@dataclass
class Hashtag:
    """Represents a hashtag suggestion with scoring metadata."""

    tag: str
    popularity: int  # Relative popularity metric (0-100)
    competition: int  # Lower is better (0-100)
    relevance: int  # How relevant the tag is to the topic (0-100)


class HashtagOptimizer:
    """Generates and scores hashtags for different platforms."""

    def __init__(self) -> None:
        # Example static database of hashtags by topic.  In a real
        # implementation this could be loaded from a file or API.
        self.topic_tags: Dict[str, List[Hashtag]] = {
            "nail art": [
                Hashtag("#nailart", popularity=90, competition=70, relevance=95),
                Hashtag("#nails", popularity=85, competition=80, relevance=90),
                Hashtag("#manicure", popularity=70, competition=60, relevance=85),
            ],
            "toy reviews": [
                Hashtag("#toyreview", popularity=60, competition=50, relevance=90),
                Hashtag("#kidstoys", popularity=75, competition=65, relevance=80),
            ],
            "cooking": [
                Hashtag("#cookingtips", popularity=65, competition=55, relevance=85),
                Hashtag("#kitchenhacks", popularity=80, competition=60, relevance=80),
            ],
        }

    def suggest(self, topic: str, count: int = 3) -> List[str]:
        """Suggest a list of hashtags for a given topic.

        Args:
            topic: The topic to generate hashtags for.
            count: Number of suggestions to return.

        Returns:
            A list of hashtag strings sorted by weighted score.
        """
        tags = self.topic_tags.get(topic.lower(), [])
        if not tags:
            return []
        # Compute a simple weighted score: high popularity and relevance,
        # lower competition preferred.  Weight popularity and relevance
        # higher than competition.
        scored = [
            (
                ht.tag,
                (ht.popularity * 0.4 + ht.relevance * 0.4 + (100 - ht.competition) * 0.2),
            )
            for ht in tags
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [tag for tag, _ in scored[:count]]

    def suggest_metricool(self, topic: str, count: int = 5) -> List[str]:
        """Suggest hashtags based on Metricool account overview.

        This helper attempts to fetch trending or top hashtags from
        the Metricool API using the configured account overview.  If
        Metricool credentials are not configured or the response does
        not contain any hashtag information, the method falls back to
        the static suggestions defined by :meth:`suggest`.

        Args:
            topic: Topic name used as a fallback if Metricool returns
                no data.
            count: Maximum number of hashtag suggestions to return.

        Returns:
            A list of hashtag strings beginning with ``#``.  If
            Metricool is unavailable the list may be empty.
        """
        try:
            # Import lazily to avoid pulling in dependencies unless needed
            from integrations.metricool import get_overview  # type: ignore
        except Exception:
            # If Metricool integration is missing, fall back to static
            return self.suggest(topic, count)
        try:
            overview = get_overview()
            if not overview:
                return self.suggest(topic, count)
            # Attempt to find keys that may contain hashtag data.  Metricool's
            # response structure is not strictly defined here, so we scan
            # for any list under keys containing 'hashtags'.
            hashtags: List[str] = []
            for key, value in overview.items():
                if isinstance(key, str) and 'hashtag' in key.lower() and isinstance(value, list):
                    # Extract the tag names from each item.  Items may be
                    # dictionaries with 'name' or 'tag' fields or may be
                    # plain strings.
                    for item in value:
                        tag = None
                        if isinstance(item, dict):
                            # Prefer 'name' or 'tag' keys
                            tag = item.get('name') or item.get('tag') or item.get('term')
                        elif isinstance(item, str):
                            tag = item
                        if tag:
                            tag_str = tag if tag.startswith('#') else f"#{tag}"
                            hashtags.append(tag_str)
                    # Stop scanning once we find a hashtag list
                    break
            # Return the top N unique hashtags preserving order
            if hashtags:
                seen: set[str] = set()
                deduped = []
                for ht in hashtags:
                    if ht not in seen:
                        deduped.append(ht)
                        seen.add(ht)
                    if len(deduped) >= count:
                        break
                return deduped
            # Fallback: use static suggestions
            return self.suggest(topic, count)
        except Exception:
            # In case of any error (network, parsing etc.), fall back
            return self.suggest(topic, count)

    def suggest_dynamic(self, topic: str, count: int = 5, cfg: Union[Dict[str, Any], None] = None) -> List[str]:
        """Suggest hashtags using real‑time trend data when available.

        This convenience method attempts to fetch trending keywords for
        the supplied topic using Nova's ``TrendScanner``.  If the
        network call fails or the trend scanner is not configured
        correctly, it falls back to the static suggestions provided
        by :meth:`suggest`.

        Args:
            topic: Topic or seed keyword to scan for trends.
            count: Maximum number of hashtags to return.
            cfg: Optional configuration dictionary for the trend
                scanner.  If omitted, a basic configuration is
                constructed.

        Returns:
            A list of hashtag strings derived from trending keywords.
        """
        # If a specific hashtag service is requested via environment
        # variables, defer to that integration.  For example, if
        # ``HASHTAG_SERVICE`` is set to ``"metricool"``, we will use
        # Metricool to derive trending hashtags.  Additional services
        # could be supported in future by adding corresponding branches.
        import os
        service = os.getenv('HASHTAG_SERVICE', '').lower()
        if service == 'metricool':
            return self.suggest_metricool(topic, count=count)
        # Default: attempt to use the TrendScanner for dynamic trends
        try:
            # Import here to avoid circular dependency at module load time
            import asyncio
            from nova.governance.trend_scanner import TrendScanner  # type: ignore

            # Build a minimal configuration; allow overrides via cfg
            default_cfg = {
                'rpm_multiplier': 1.0,
                'top_n': count,
                # Disable optional sources by default for speed
                'use_tiktok': False,
                'use_vidiq': False,
                'use_youtube': False,
                'use_google_ads': False,
                'use_gwi': False,
                'use_affiliate': False,
            }
            if cfg:
                default_cfg.update(cfg)
            scanner = TrendScanner(default_cfg)
            # Run the asynchronous scan synchronously
            trends = asyncio.run(scanner.scan([topic]))
            if trends:
                return self.suggest_from_trends(trends, count=count)
        except Exception:
            # Ignore any exceptions (network errors, policy enforcement,
            # missing dependencies) and fallback to static suggestions
            pass
        # Fallback: return static suggestions
        return self.suggest(topic, count)

    def suggest_from_trends(self, trends: Iterable[Dict[str, Any]], count: int = 5) -> List[str]:
        """Suggest hashtags based on a list of trend objects.

        This helper converts trend keywords into hashtag strings and ranks
        them using the provided interest or projected RPM scores.  The
        higher the score, the higher the priority in the returned list.

        Args:
            trends: An iterable of dictionaries representing trend entries.
                Each entry should contain a 'keyword' or 'term' key and
                optionally an 'interest' or 'projected_rpm' value to
                indicate relative popularity.
            count: Maximum number of hashtags to return.

        Returns:
            A list of hashtag strings (e.g. '#example') sorted by
            descending score.  Duplicate hashtags are deduplicated with
            the highest score preserved.  If no valid trends are
            provided, an empty list is returned.
        """
        tags: List[Tuple[str, float]] = []
        for item in trends:
            # Determine the raw keyword or term
            key: Any = item.get("keyword") or item.get("term")
            if not key or not isinstance(key, str):
                continue
            # Normalise the keyword into a hashtag-friendly slug by
            # stripping non-alphanumeric characters and whitespace
            slug = '#' + ''.join(ch for ch in key if ch.isalnum())
            # Determine the score; prefer projected RPM over interest
            raw_score: Any = item.get('projected_rpm', item.get('interest', 1.0))
            try:
                score = float(raw_score)
            except Exception:
                score = 1.0
            tags.append((slug, score))
        # Deduplicate hashtags, keeping the highest score for each slug
        dedup: Dict[str, float] = {}
        for slug, score in tags:
            if slug not in dedup or score > dedup[slug]:
                dedup[slug] = score
        # Sort by score descending
        sorted_tags = sorted(dedup.items(), key=lambda x: x[1], reverse=True)
        # Return only the hashtag strings, limited to the requested count
        return [slug for slug, _ in sorted_tags[:count]]
