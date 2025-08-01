"""RPM Leaderboard Module.

This module defines data structures and helper functions to maintain
a leaderboard of prompt performance based on revenue per thousand
views (RPM), average view duration (AVD) and click-through rate
(CTR).  It can ingest metric dictionaries, cluster prompts by
audience demographic and identify underperformers for automatic
retirement.

The leaderboard uses simple weighted scoring to rank prompts.  In
practice, this could be replaced with a more sophisticated ML
model or integrated with external analytics services.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class PromptMetrics:
    """Stores performance metrics for a given prompt."""

    prompt_id: str
    rpm: float
    avd: float  # average view duration in seconds
    ctr: float  # click-through rate (0-1)
    audience_country: str
    audience_age: str


class PromptLeaderboard:
    """Maintains a leaderboard of prompts ranked by RPM and engagement."""

    def __init__(self) -> None:
        self.metrics: Dict[str, PromptMetrics] = {}

    def ingest_metrics(self, metrics: List[Dict]) -> None:
        """Load a list of metric dictionaries into the leaderboard.

        Args:
            metrics: A list of dictionaries with keys matching
                ``PromptMetrics`` fields.
        """
        for m in metrics:
            pm = PromptMetrics(**m)
            self.metrics[pm.prompt_id] = pm

    def rank_prompts(self) -> List[Tuple[str, float]]:
        """Return a list of prompt IDs ranked by a weighted score.

        Returns:
            A list of tuples (prompt_id, score) sorted descending.
        """
        scores = {}
        for pid, pm in self.metrics.items():
            # Weighted score emphasises RPM and AVD; CTR has lower weight
            score = pm.rpm * 0.5 + pm.avd * 0.3 + pm.ctr * 100 * 0.2
            scores[pid] = score
        return sorted(scores.items(), key=lambda kv: kv[1], reverse=True)

    def cluster_by_audience(self) -> Dict[str, List[str]]:
        """Cluster prompts by dominant audience segments (country + age)."""
        clusters: Dict[str, List[str]] = {}
        for pid, pm in self.metrics.items():
            key = f"{pm.audience_country}_{pm.audience_age}"
            clusters.setdefault(key, []).append(pid)
        return clusters

    def retire_bottom_percent(self, percent: float) -> List[str]:
        """Identify and remove the bottom percentage of performers.

        Args:
            percent: The fraction (0-100) of prompts to retire.

        Returns:
            A list of retired prompt IDs.
        """
        ranked = self.rank_prompts()
        num_to_retire = int(len(ranked) * (percent / 100.0))
        retired_ids = [pid for pid, _ in ranked[-num_to_retire:]]
        for pid in retired_ids:
            self.metrics.pop(pid, None)
        return retired_ids
