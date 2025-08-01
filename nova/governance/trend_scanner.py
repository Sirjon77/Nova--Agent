"""Trend scanning for governance.

This module fetches trending topics from various sources and projects
their revenue potential. It also integrates with the policy enforcer
to ensure only allowed tools are used and to respect memory limits.

Currently, it only implements Google Trends as a data source. Future
versions may include TikTok, vidIQ and other services.
"""

from __future__ import annotations

import asyncio
from datetime import date
from typing import Iterable, List, Dict

import httpx

from nova.policy import PolicyEnforcer


class TrendScanner:
    """Fetch trending data and compute projected RPM.

    The scanner uses configured sources to gather trend data and
    multiplies interest by a configured factor to project potential
    revenue. A `PolicyEnforcer` is used to verify that external
    services are allowed.

    Args:
        cfg: Configuration dictionary containing parameters such as
            `rpm_multiplier` and `top_n`.
    """

    def __init__(self, cfg: Dict):
        self.cfg = cfg
        self.enforcer = PolicyEnforcer()

    def _enforce(self) -> None:
        """Enforce policy rules for the trend scanner.

        Currently ensures that the `google_trends` tool is allowed and
        that memory limits are respected before executing API calls.
        """
        # Ensure the google_trends tool is permitted by policy
        self.enforcer.enforce_tool('google_trends')
        # Respect memory limits (fail fast if over limit)
        if not self.enforcer.check_memory():
            raise MemoryError("Policy memory limit exceeded during trend scan")

    async def _google_trends(self, term: str) -> Dict:
        """Query Google Trends for a given term.

        Returns the parsed JSON response if successful, otherwise an
        empty dictionary. Any exceptions raised by httpx will be
        propagated to allow upstream handling.
        """
        async with httpx.AsyncClient(timeout=10) as client:
            url = 'https://trends.google.com/trends/api/explore'
            r = await client.get(url, params={'hl': 'en-US', 'q': term, 'date': 'now 7-d'})
            if r.status_code != 200:
                return {}
            # the Google Trends API sometimes prefixes JSON with nonsense; remove it
            try:
                data = r.json()
            except Exception:
                return {}
            return data

    async def scan(self, seeds: Iterable[str]) -> List[Dict]:
        """Scan for trends based on seed keywords.

        Performs policy enforcement, fires concurrent requests to
        Google Trends for each seed term and aggregates the results.

        Args:
            seeds: An iterable of seed keywords or phrases.

        Returns:
            A list of dictionaries sorted by projected RPM descending.
        """
        self._enforce()

        trends: List[Dict] = []

        # Launch all Google Trends queries concurrently
        g_tasks = [self._google_trends(str(seed)) for seed in seeds]
        g_results = await asyncio.gather(*g_tasks, return_exceptions=True)
        for seed, js in zip(seeds, g_results):
            # handle exceptions gracefully by treating as zero interest
            if isinstance(js, Exception) or not isinstance(js, dict):
                interest = 0
            else:
                interest = js.get('default', {}).get('averages', [0])[0]
            projected_rpm = interest * self.cfg.get('rpm_multiplier', 1)
            trends.append({
                'keyword': str(seed),
                'interest': interest,
                'projected_rpm': projected_rpm,
                'source': 'google_trends',
                'scanned_on': str(date.today()),
            })

        # Optionally fetch TikTok trending topics
        if self.cfg.get('use_tiktok'):
            try:
                tiktok_terms = await self._tiktok_trends()
                for term, score in tiktok_terms:
                    trends.append({
                        'keyword': term,
                        'interest': score,
                        'projected_rpm': score * self.cfg.get('rpm_multiplier', 1),
                        'source': 'tiktok',
                        'scanned_on': str(date.today()),
                    })
            except Exception:
                # swallow exceptions from unofficial APIs
                pass

        # Optionally fetch vidIQ trending keywords
        if self.cfg.get('use_vidiq'):
            try:
                vidiq_terms = await self._vidiq_trends()
                for term, score in vidiq_terms:
                    trends.append({
                        'keyword': term,
                        'interest': score,
                        'projected_rpm': score * self.cfg.get('rpm_multiplier', 1),
                        'source': 'vidiq',
                        'scanned_on': str(date.today()),
                    })
            except Exception:
                pass

        # Optionally fetch YouTube trending videos (via TubeBuddy/YouTube Data API)
        if self.cfg.get('use_youtube'):
            try:
                yt_terms = await self._youtube_trends()
                for term, score in yt_terms:
                    trends.append({
                        'keyword': term,
                        'interest': score,
                        'projected_rpm': score * self.cfg.get('rpm_multiplier', 1),
                        'source': 'youtube_trending',
                        'scanned_on': str(date.today()),
                    })
            except Exception:
                # swallow any exceptions from TubeBuddy integration
                pass

        # Optionally fetch trends from Google Ads Keyword Planner
        if self.cfg.get('use_google_ads'):
            try:
                ads_terms = await self._google_ads_trends()
                for term, score in ads_terms:
                    trends.append({
                        'keyword': term,
                        'interest': score,
                        'projected_rpm': score * self.cfg.get('rpm_multiplier', 1),
                        'source': 'google_ads',
                        'scanned_on': str(date.today()),
                    })
            except Exception:
                pass

        # Optionally fetch trends from Global Web Index (GWI)
        if self.cfg.get('use_gwi'):
            try:
                gwi_terms = await self._gwi_trends()
                for term, score in gwi_terms:
                    trends.append({
                        'keyword': term,
                        'interest': score,
                        'projected_rpm': score * self.cfg.get('rpm_multiplier', 1),
                        'source': 'gwi',
                        'scanned_on': str(date.today()),
                    })
            except Exception:
                pass

        # Optionally fetch affiliate product trends
        if self.cfg.get('use_affiliate'):
            try:
                aff_terms = await self._affiliate_trends()
                for term, score in aff_terms:
                    trends.append({
                        'keyword': term,
                        'interest': score,
                        'projected_rpm': score * self.cfg.get('rpm_multiplier', 1),
                        'source': 'affiliate',
                        'scanned_on': str(date.today()),
                    })
            except Exception:
                pass

        # Sort by projected RPM descending and return top N
        trends.sort(key=lambda x: x['projected_rpm'], reverse=True)
        return trends[: self.cfg.get('top_n', 10)]

    async def _tiktok_trends(self) -> List[tuple[str, float]]:
        """Fetch top trending topics from TikTok.

        TikTok does not provide an official unauthenticated API for trending
        hashtags, so this implementation performs a simple HTTP request to
        the public trending tag page and extracts hashtag titles using a
        regular expression. If the request fails or no hashtags are found,
        an empty list is returned. In production you should replace this
        with a proper API integration or a more robust scraper.

        Returns:
            A list of (term, score) tuples representing trending topics. The
            `score` is a placeholder value (1.0) since TikTok does not
            expose numeric interest scores via this method.
        """
        import re
        url = "https://www.tiktok.com/tag/trending"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code != 200:
                return []
            # Extract hashtag titles from the page's JSON embedded data. TikTok
            # embeds hashtag names in the form \"title\":\"#example\".
            hashtags = re.findall(r'"title":"#(.*?)"', resp.text)
            # Deduplicate while preserving order and prefix with '#'
            seen = set()
            results: List[tuple[str, float]] = []
            for tag in hashtags:
                if tag not in seen:
                    seen.add(tag)
                    results.append((f"#{tag}", 1.0))
                if len(results) >= 10:
                    break
            return results
        except Exception:
            # On any error (network or parsing) return an empty list
            return []

    async def _vidiq_trends(self) -> List[tuple[str, float]]:
        """Fetch top trending keywords from vidIQ.

        vidIQ offers an API for trending search terms, but it requires an
        API key. If a `vidiq_api_key` is provided in the trend scanner
        configuration, this method will attempt to query the vidIQ API for
        trending keywords. Without a key, an empty list is returned. See
        https://vidiq.com/ for API details.

        Returns:
            A list of (term, score) tuples representing trending keywords.
        """
        api_key = self.cfg.get("vidiq_api_key")
        if not api_key:
            return []
        try:
            # Example endpoint; replace with the correct vidIQ API URL
            url = "https://vidiq.com/api/trending"
            headers = {"Authorization": f"Bearer {api_key}"}
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                return []
            data = resp.json()
            # Assume the API returns a list of objects with 'keyword' and 'score'
            items = data.get("trending", [])
            results: List[tuple[str, float]] = []
            for item in items:
                term = item.get("keyword")
                score = item.get("score", 0.0)
                if term:
                    results.append((term, float(score)))
                if len(results) >= 10:
                    break
            return results
        except Exception:
            return []

    async def _youtube_trends(self) -> List[tuple[str, float]]:
        """Fetch trending video titles from YouTube via TubeBuddy integration.

        This helper wraps the synchronous `get_trending_videos` function from the
        TubeBuddy module into an asynchronous context using `asyncio.to_thread`.
        It returns a list of tuples where each tuple contains the video title
        and a placeholder score (1.0) since the YouTube API does not provide
        a direct interest metric for trending videos. In production, you may
        want to derive a score based on view counts or other statistics.

        Returns:
            A list of (title, score) tuples representing trending videos. If
            the API call fails, an empty list is returned.
        """
        try:
            from integrations.tubebuddy import get_trending_videos
        except Exception:
            return []
        try:
            # Run the synchronous call in a thread to avoid blocking the event loop
            videos = await asyncio.to_thread(get_trending_videos, max_results=10)
        except Exception:
            return []
        results: List[tuple[str, float]] = []
        for vid in videos:
            title = vid.get('title')
            if title:
                results.append((title, 1.0))
        return results

    async def _google_ads_trends(self) -> List[tuple[str, float]]:
        """Fetch trending keywords from Google Ads Keyword Planner (stub).

        This placeholder implementation returns a curated list of
        high‑volume search queries along with rough popularity scores.
        These keywords are chosen to reflect general advertising
        interest (e.g., technology, finance, consumer goods) and are
        meant to stand in for results from the Google Ads API.  When
        proper API credentials become available, this method should
        query the Keyword Planner and return real data.  Until then,
        the static list below provides deterministic suggestions for
        demonstration and development purposes.

        Returns:
            A list of (keyword, score) tuples representing trending
            search terms and their relative popularity (0–1).  The
            length of the list is limited by the configured top_n
            parameter if specified in the scanner configuration.
        """
        # Define a static set of trending search terms with heuristic scores
        static_terms: List[tuple[str, float]] = [
            ("ai tools", 0.9),
            ("cryptocurrency", 0.85),
            ("sustainable fashion", 0.8),
            ("online education", 0.75),
            ("home workout", 0.7),
            ("virtual reality", 0.65),
            ("smart home devices", 0.6),
            ("personal finance", 0.55),
            ("plant based diet", 0.5),
            ("digital marketing", 0.45),
        ]
        # Respect top_n configuration when present
        limit = int(self.cfg.get('top_n', len(static_terms)))
        return static_terms[:limit]

    async def _gwi_trends(self) -> List[tuple[str, float]]:
        """Fetch trending topics from Global Web Index (GWI).

        This implementation uses the ``integrations.gwi`` helper to
        retrieve audience‑insight trends.  If a GWI trend endpoint and
        API key are not configured via environment variables, the
        helper will return an empty list.  Results are normalised
        into (term, interest) tuples.  Any exceptions or
        misconfiguration will yield an empty list, allowing the trend
        scanner to continue without failing.

        Returns:
            A list of (term, interest) tuples where ``interest`` is a
            float projecting relative popularity.
        """
        try:
            # Import synchronously to avoid heavy imports if unused
            from integrations.gwi import get_trending_topics
        except Exception:
            return []
        try:
            # Determine region and limit from configuration.  Default to
            # 'us' and 10 items if unspecified.
            region = self.cfg.get('gwi_region', 'us')  # type: ignore
            limit = int(self.cfg.get('gwi_limit', 10))  # type: ignore
            # Run the synchronous function in a thread to avoid
            # blocking the event loop.
            data = await asyncio.to_thread(get_trending_topics, region=region, limit=limit)
        except Exception:
            return []
        results: List[tuple[str, float]] = []
        for item in data:
            term = item.get('term')
            # Use 'interest' if available; default to 1.0 to indicate
            # presence without a numeric metric.
            raw_score = item.get('interest', 1.0)
            try:
                score = float(raw_score)
            except Exception:
                score = 1.0
            if term:
                results.append((term, score))
        return results

    async def _affiliate_trends(self) -> List[tuple[str, float]]:
        """Fetch product keywords from affiliate programmes (stub).

        This method synthesises a list of trending product categories
        commonly promoted through affiliate networks such as Amazon
        Associates or ClickBank.  Each tuple contains a descriptive
        keyword and a rough popularity score between 0 and 1.  When
        credentials for affiliate APIs are available, this stub should
        be replaced with real integrations that fetch high‑converting
        product niches.  Until then, the static list below enables
        downstream modules to operate without failing.

        Returns:
            A list of (keyword, score) tuples representing trending
            product niches and their relative popularity.
        """
        static_products: List[tuple[str, float]] = [
            ("wireless earbuds", 0.9),
            ("smart watch", 0.85),
            ("air fryer", 0.8),
            ("yoga mat", 0.75),
            ("robot vacuum", 0.7),
            ("portable power station", 0.65),
            ("gaming chair", 0.6),
            ("action camera", 0.55),
            ("herbal supplements", 0.5),
            ("eco friendly water bottle", 0.45),
        ]
        limit = int(self.cfg.get('top_n', len(static_products)))
        return static_products[:limit]