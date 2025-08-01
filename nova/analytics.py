"""Analytics helper functions for prompt performance metrics.

This module provides lightweight utilities to summarise and analyse
performance metrics for prompts.  The functions operate on a list of
metric dictionaries that contain at minimum the following fields:

    - ``prompt_id``: Unique identifier for the prompt.
    - ``rpm``: Revenue per thousand views (float).
    - ``avd``: Average view duration in seconds (float).
    - ``ctr``: Click‑through rate (0‑1 range).
    - ``audience_country``: Country code of the audience (string).
    - ``audience_age``: Age bracket of the audience (string).
    - ``views`` (optional): Total number of views for the prompt.

The functions return summary statistics, top performers and RPM
groupings by audience segment.  These helpers complement the
``PromptLeaderboard`` class by providing insights into prompt
performance beyond simple ranking.

Note: These helpers do not persist any state and can be used safely
in both synchronous and asynchronous contexts.
"""

from __future__ import annotations

from typing import List, Dict, Any


def aggregate_metrics(metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate performance metrics across all prompts.

    Args:
        metrics: List of dictionaries containing prompt metrics.  Each
            dictionary should include at least ``rpm`` and may include
            ``views`` to compute total views.

    Returns:
        A dictionary with the total number of entries, sum of views
        (if provided) and the average RPM across all prompts.
    """
    total = len(metrics)
    total_views = 0
    total_rpm = 0.0
    for m in metrics:
        # Sum RPM and views if available
        total_rpm += float(m.get("rpm", 0))
        if "views" in m:
            total_views += float(m.get("views", 0))
    average_rpm = total_rpm / total if total > 0 else 0.0
    return {"count": total, "total_views": total_views, "average_rpm": average_rpm}


def top_prompts(metrics: List[Dict[str, Any]], n: int = 5) -> List[Dict[str, Any]]:
    """Return the top N prompts sorted by RPM descending.

    Args:
        metrics: List of prompt metric dictionaries.
        n: Number of top prompts to return.

    Returns:
        A list of the top N metric dictionaries sorted by RPM.
    """
    sorted_metrics = sorted(metrics, key=lambda m: float(m.get("rpm", 0)), reverse=True)
    return sorted_metrics[:n]


def rpm_by_audience(metrics: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Group average RPM by audience country and age bracket.

    Args:
        metrics: List of prompt metric dictionaries.  Each should
            include ``audience_country`` and ``audience_age`` keys.

    Returns:
        A dictionary keyed by ``country_age`` string with values
        containing the average RPM and count of prompts for that
        audience segment.
    """
    groups: Dict[str, Dict[str, Any]] = {}
    for m in metrics:
        country = m.get("audience_country", "UNK") or "UNK"
        age = m.get("audience_age", "UNK") or "UNK"
        key = f"{country}_{age}"
        g = groups.setdefault(key, {"total_rpm": 0.0, "count": 0})
        g["total_rpm"] += float(m.get("rpm", 0))
        g["count"] += 1
    # Convert total RPM to average
    for key, g in groups.items():
        count = g["count"]
        g["average_rpm"] = g["total_rpm"] / count if count > 0 else 0.0
        del g["total_rpm"]
    return groups