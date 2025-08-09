"""
Scoring engine for channel/niche health.

Implements multi-metric composite scoring using Z-score normalization and
configurable weights/thresholds loaded from a YAML config file.
"""

from __future__ import annotations

import math
from typing import Dict, List, Any

import yaml


# Load configuration (weights, thresholds) from YAML
with open("governance_config.yaml", "r") as _f:
    _config = yaml.safe_load(_f) or {}

METRIC_WEIGHTS: Dict[str, float] = _config.get("metrics", {})
THRESHOLDS: Dict[str, float] = _config.get("thresholds", {})


def compute_channel_scores(channels_data: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Compute a composite health score for each channel using weighted Z-normalized metrics.

    Args:
        channels_data: list of dicts, each with channel metrics
            e.g. {"name": ..., "RPM": ..., "growth": ..., "engagement": ...}

    Returns:
        dict mapping channel name -> composite score
    """
    metrics = list(METRIC_WEIGHTS.keys())
    if not channels_data or not metrics:
        return {}

    # Calculate means per metric
    n = len(channels_data)
    means: Dict[str, float] = {m: 0.0 for m in metrics}
    stds: Dict[str, float] = {m: 0.0 for m in metrics}

    for m in metrics:
        total = 0.0
        for channel in channels_data:
            total += float(channel.get(m, 0.0) or 0.0)
        means[m] = total / n if n else 0.0

    # Population standard deviation
    for m in metrics:
        var = 0.0
        mean_val = means[m]
        for channel in channels_data:
            val = float(channel.get(m, 0.0) or 0.0)
            diff = val - mean_val
            var += diff * diff
        var = var / n if n else 0.0
        std = math.sqrt(var)
        stds[m] = std if std != 0.0 else 1.0  # avoid div-by-zero

    # Compute Z-score weighted composite for each channel
    scores: Dict[str, float] = {}
    for channel in channels_data:
        composite = 0.0
        for m in metrics:
            val = float(channel.get(m, 0.0) or 0.0)
            z = (val - means[m]) / stds[m]
            composite += z * float(METRIC_WEIGHTS.get(m, 0.0) or 0.0)
        scores[channel.get("name", "<unknown>")] = composite

    return scores


def classify_channel(score: float) -> str:
    """Classify a channel based on its composite score using configured thresholds."""
    promote = THRESHOLDS.get("promote")
    retire = THRESHOLDS.get("retire")
    if promote is not None and score >= float(promote):
        return "promote"
    if retire is not None and score <= float(retire):
        return "retire"
    return "watch"


