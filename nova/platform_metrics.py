"""Platform-specific performance tracking.

This module implements a simple storage layer for recording
metrics per platform and country.  Each entry captures
information such as RPM, views, CTR and retention for a given
prompt on a particular platform.  The storage is persisted to a
JSON file under the module's data directory.  Helper functions
allow recording new metrics, retrieving a leaderboard of top
performers and retiring underperforming prompts by platform.

It is intentionally lightweight and uses the same conceptual
approach as :mod:`prompt_metrics` so that it can be swapped out
for a more robust database in the future.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Tuple


# Directory for persisting platform metrics.  Located adjacent
# to this module in a ``data`` subdirectory.
_DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
_DATA_PATH = os.path.join(_DATA_DIR, 'platform_metrics.json')


@dataclass
class PlatformMetric:
    """Encapsulates a performance datapoint for a prompt on a platform."""

    prompt_id: str
    platform: str
    rpm: float
    views: int
    ctr: float  # click-through rate (0–1)
    retention: float  # average retention (0–1)
    country: str = 'US'


def _load_platform_data() -> Dict[str, Any]:
    """Load the platform metrics JSON from disk.

    Returns:
        A nested dictionary keyed by prompt_id containing per-platform
        statistics and lists of recorded metrics.
    """
    if os.path.exists(_DATA_PATH):
        try:
            with open(_DATA_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_platform_data(data: Dict[str, Any]) -> None:
    """Persist platform metrics to disk as JSON."""
    os.makedirs(_DATA_DIR, exist_ok=True)
    with open(_DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def record_platform_metric(
    *,
    prompt_id: str,
    platform: str,
    rpm: float,
    views: int,
    ctr: float,
    retention: float,
    country: str = 'US',
) -> None:
    """Record a new platform-specific performance datapoint.

    This function appends a new record to the prompt's platform
    history and recalculates aggregate statistics per platform.  If
    the prompt or platform does not yet exist, it is created.

    Args:
        prompt_id: Identifier of the prompt.
        platform: Name of the platform (e.g. 'youtube').
        rpm: Revenue per thousand impressions.
        views: Raw view count.
        ctr: Click-through rate.
        retention: Average retention fraction.
        country: Country code of the audience (optional).
    """
    data = _load_platform_data()
    prompt_dict = data.setdefault(prompt_id, {})
    platform_key = platform.lower()
    stats = prompt_dict.setdefault(platform_key, {
        'records': [],
        'avg_rpm': 0.0,
        'avg_views': 0.0,
        'avg_ctr': 0.0,
        'avg_retention': 0.0,
        'country_counts': {},
    })
    # Append the new record
    record = PlatformMetric(
        prompt_id=prompt_id,
        platform=platform_key,
        rpm=rpm,
        views=views,
        ctr=ctr,
        retention=retention,
        country=country,
    )
    stats['records'].append(asdict(record))
    # Update aggregates
    recs = stats['records']
    n = len(recs)
    if n:
        total_rpm = sum(r['rpm'] for r in recs)
        total_views = sum(r['views'] for r in recs)
        total_ctr = sum(r['ctr'] for r in recs)
        total_ret = sum(r['retention'] for r in recs)
        stats['avg_rpm'] = total_rpm / n
        stats['avg_views'] = total_views / n
        stats['avg_ctr'] = total_ctr / n
        stats['avg_retention'] = total_ret / n
    # Update country counts
    country_counts: Dict[str, int] = stats.get('country_counts', {})
    country_counts[country] = country_counts.get(country, 0) + views
    stats['country_counts'] = country_counts
    # Save back
    prompt_dict[platform_key] = stats
    data[prompt_id] = prompt_dict
    _save_platform_data(data)


def get_platform_leaderboard(metric: str = 'avg_rpm', top_n: int = 10) -> List[Tuple[str, float]]:
    """Return a leaderboard of (prompt_id, score) aggregated across platforms.

    Prompts are ranked by summing the specified metric across all
    platforms.  For example, specifying ``metric='avg_rpm'`` will
    compute the total average RPM of a prompt across YouTube,
    Instagram and TikTok and rank the prompts by that sum.

    Args:
        metric: Aggregate metric to use ('avg_rpm', 'avg_views', etc.).
        top_n: Number of prompts to return.

    Returns:
        A list of tuples (prompt_id, score) sorted descending.
    """
    data = _load_platform_data()
    scores: Dict[str, float] = {}
    for prompt_id, platforms in data.items():
        total = 0.0
        for stats in platforms.values():
            total += float(stats.get(metric, 0.0))
        scores[prompt_id] = total
    return sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:top_n]


def retire_underperforming(metric: str = 'avg_rpm', threshold: float = 1.0) -> List[str]:
    """Identify prompts that fall below the threshold on all platforms.

    Args:
        metric: Aggregate metric to evaluate (e.g. 'avg_rpm').
        threshold: Minimum acceptable value.  Prompts with all
            platform averages below this threshold will be retired.

    Returns:
        A list of prompt IDs that were removed from the dataset.
    """
    data = _load_platform_data()
    to_retire: List[str] = []
    for prompt_id, platforms in list(data.items()):
        # Determine the maximum metric value across platforms for this prompt
        max_metric = 0.0
        for stats in platforms.values():
            val = float(stats.get(metric, 0.0))
            if val > max_metric:
                max_metric = val
        if max_metric < threshold:
            to_retire.append(prompt_id)
            data.pop(prompt_id, None)
    if to_retire:
        _save_platform_data(data)
    return to_retire


def get_country_heatmap(metric: str = 'avg_views') -> Dict[str, float]:
    """Aggregate performance metrics by country across all prompts and platforms.

    This helper iterates over the stored platform metrics and sums the
    requested metric for each country.  When ``metric`` is ``'avg_views'``
    (the default), the heatmap reflects the total number of views per
    country across all prompts and platforms.  For other metrics (e.g.
    ``'avg_rpm'``, ``'avg_ctr'``, ``'avg_retention'``), the heatmap
    sums the average value reported for each platform without weighting
    by view count.  If no data exist, an empty dictionary is returned.

    Args:
        metric: The aggregate metric to accumulate by country.

    Returns:
        A mapping of country codes to aggregated metric values.
    """
    data = _load_platform_data()
    heatmap: Dict[str, float] = {}
    for prompt_id, platforms in data.items():
        for stats in platforms.values():
            # For views we use the country_counts dictionary; for other
            # metrics we simply add the metric value once per platform.
            if metric == 'avg_views':
                country_counts = stats.get('country_counts', {})
                for country, views in country_counts.items():
                    heatmap[country] = heatmap.get(country, 0.0) + float(views)
            else:
                val = float(stats.get(metric, 0.0))
                # If country_counts exist, spread the value across countries
                countries = stats.get('country_counts', {}).keys() or ['US']
                for country in countries:
                    heatmap[country] = heatmap.get(country, 0.0) + val
    return heatmap
