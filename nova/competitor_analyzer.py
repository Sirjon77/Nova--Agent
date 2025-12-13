"""Competitor Analysis and Hidden Prompt Mining.

This module provides helper classes to analyse competitors and
discover underutilised prompt structures.  It integrates with the
``TrendScanner`` to fetch trending keywords and with the
``PromptDiscoverer`` to generate novel prompt templates.  The
``CompetitorAnalyzer`` class synthesises competitor benchmarking
statistics using heuristic scores when real data is unavailable.

Example usage::

    from nova.competitor_analyzer import CompetitorAnalyzer
    import asyncio

    cfg = {"rpm_multiplier": 1.0, "top_n": 10}
    analyzer = CompetitorAnalyzer(cfg)
    results = asyncio.run(analyzer.benchmark_competitors(["ai", "fitness"], count=5))
    for comp in results:
        print(comp)

"""

from __future__ import annotations

from typing import Iterable, List, Dict, Any

from nova.governance.trend_scanner import TrendScanner
from nova.hidden_prompt_discovery import PromptDiscoverer, PromptTemplate


class CompetitorAnalyzer:
    """Analyse competitors and mine hidden prompts from trending data.

    This class utilises the ``TrendScanner`` to obtain high-interest
    keywords and synthesises placeholder competitor performance
    statistics in lieu of real analytics.  It also wraps the
    ``PromptDiscoverer`` to generate new prompt structures from
    seed roles, domains, outcomes and niches.  When integrated
    with live analytics (e.g., watch time, CTR), these methods can
    be extended to provide data‑driven benchmarks and recommendations.
    """

    def __init__(self, cfg: Dict[str, Any]) -> None:
        # Store configuration for the underlying trend scanner
        self.cfg = cfg

    async def benchmark_competitors(self, seeds: Iterable[str], count: int = 10) -> List[Dict[str, Any]]:
        """Benchmark competitor keywords based on trending data.

        Given a list of seed topics, fetch trending keywords via
        ``TrendScanner`` and fabricate competitor statistics
        (interest, projected RPM).  Since real competitor
        analytics (e.g., channel names, subscriber counts) are not
        available in this context, competitor identifiers are
        numbered sequentially and scores are derived directly from
        trend data.  The returned list is ordered by projected RPM
        descending.

        Args:
            seeds: Seed keywords or phrases used to query the trend scanner.
            count: Maximum number of competitor entries to return.

        Returns:
            A list of dictionaries containing 'competitor', 'keyword',
            'interest' and 'projected_rpm' fields.
        """
        scanner = TrendScanner(self.cfg)
        # Perform asynchronous trend scan on provided seeds
        trends = await scanner.scan(seeds)
        results: List[Dict[str, Any]] = []
        for idx, tr in enumerate(trends[:count], start=1):
            keyword = tr.get('keyword')
            interest = tr.get('interest', 0.0)
            projected_rpm = tr.get('projected_rpm', 0.0)
            results.append({
                'competitor': f"Competitor {idx}",
                'keyword': keyword,
                'interest': interest,
                'projected_rpm': projected_rpm,
            })
        return results

    def discover_hidden_prompts(
        self,
        roles: List[str],
        domains: List[str],
        outcomes: List[str],
        niches: List[str],
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Generate hidden prompt templates from seed parameters.

        This method wraps ``PromptDiscoverer.discover_prompts`` and
        returns prompt structures in a serialisable form.  Use this
        to populate the prompt vault with novel prompt skeletons.

        Args:
            roles: A list of expert roles (e.g. "growth hacker").
            domains: A list of domains or industries (e.g. "AI marketing").
            outcomes: Desired deliverables (e.g. "profit machine").
            niches: Target niches or audiences.
            limit: Maximum number of prompt templates to return.

        Returns:
            A list of dictionaries with 'structure', 'description'
            and 'tags' keys.
        """
        discoverer = PromptDiscoverer()
        templates: List[PromptTemplate] = discoverer.discover_prompts(
            roles, domains, outcomes, niches, limit=limit
        )
        # Convert dataclass objects to plain dicts for easier consumption
        return [
            {
                'structure': tmpl.structure,
                'description': tmpl.description,
                'tags': tmpl.tags,
            }
            for tmpl in templates
        ]