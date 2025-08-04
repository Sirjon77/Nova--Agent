"""Prompt metrics tracking and leaderboard management.

This module implements a simple storage layer for tracking the
performance of prompts over time.  Each prompt is identified by
an arbitrary key (typically a slug or the prompt text itself) and
records of RPM, views, click‑through rate (CTR) and retention
percentage can be appended.  Aggregate statistics such as
average RPM and CTR are calculated on the fly whenever new data
points are added.  A JSON file on disk persists the metrics
between runs so that historical data are not lost.

Typical usage::

    from prompt_metrics import record_prompt_metric, get_leaderboard

    # Record a new data point for a prompt
    record_prompt_metric("rpm-gold-001", rpm=4.2, views=1000,
                        ctr=0.05, retention=0.65)

    # Retrieve the top prompts sorted by average RPM
    top_prompts = get_leaderboard(metric='avg_rpm', top_n=5)

The primary goal of this module is to enable data‑driven decision
making within Nova.  Under‑performing prompts can be identified
and either retired or refactored, while high performers can be
scaled up or used as templates for future content.  Because
external analytics services (YouTube, TikTok, etc.) may not be
accessible at runtime without API keys, this local tracker offers
a lightweight alternative.  It can easily be extended to pull
metrics from real APIs once credentials are configured.
"""

from __future__ import annotations

import json
import os
import time
from typing import Dict, Any, List, Tuple, Optional, Iterable, Union

# Define the path to the JSON file used for persisting prompt metrics.
_DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
_DATA_PATH = os.path.join(_DATA_DIR, 'prompt_metrics.json')

# Path for storing raw prompt metric records.  This file contains a
# list of dictionaries, each capturing a single metric snapshot for
# a prompt.  These records enable computing aggregate statistics
# across all prompts and over time without losing historical detail.
_RECORDS_PATH = os.path.join(_DATA_DIR, 'prompt_metrics_records.json')

# Type aliases for readability

def _load_records(filepath: str = _RECORDS_PATH) -> List[Dict[str, Any]]:
    """Load the list of raw prompt metric records.

    Args:
        filepath: Location of the JSON file to load.  Defaults to
            :data:`_RECORDS_PATH`.

    Returns:
        A list of metric record dictionaries.  If the file is missing
        or corrupted, an empty list is returned.
    """
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            # On error, fall back to empty list
            return []
    return []


def _save_records(records: List[Dict[str, Any]], filepath: str = _RECORDS_PATH) -> None:
    """Persist a list of raw prompt metric records to JSON.

    Args:
        records: The list of record dictionaries to write.
        filepath: The destination JSON file.  Defaults to
            :data:`_RECORDS_PATH`.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2)


def load_metrics(filepath: Optional[str] = None) -> List[Dict[str, Any]]:
    """Public API to load all raw prompt metric records.

    This function exposes the stored records for external callers.
    It reads the JSON file from disk and returns the records as a list.

    Unlike earlier versions which captured the default file path at
    function definition time, this implementation determines the
    location dynamically.  If no ``filepath`` is provided the currently
    configured :data:`_RECORDS_PATH` is used.  This makes it possible
    to monkeypatch ``_RECORDS_PATH`` in tests and have that change
    respected when calling :func:`load_metrics` without an explicit
    argument.

    Args:
        filepath: Custom path to load records from.  If ``None`` (the
            default), the module's :data:`_RECORDS_PATH` is used.

    Returns:
        A list of metric record dictionaries.  If the file is missing
        or cannot be parsed, an empty list is returned.
    """
    # Determine which file path to load from.  Use the module-level
    # _RECORDS_PATH when no explicit path is provided.  This allows
    # tests to override the storage location by monkeypatching the
    # module variable without needing to pass the path explicitly.
    path = filepath if filepath is not None else _RECORDS_PATH
    return _load_records(path)


def save_metrics(records: List[Dict[str, Any]], filepath: Optional[str] = None) -> None:
    """Public API to persist a list of raw prompt metric records.

    Args:
        records: The list of records to write.
        filepath: Custom path to save the records.  If ``None`` (the
            default), the module's :data:`_RECORDS_PATH` is used.
    """
    path = filepath if filepath is not None else _RECORDS_PATH
    _save_records(records, path)


def _load_metrics() -> Dict[str, Any]:
    """Load the metrics JSON from disk.

    Returns:
        A dictionary keyed by prompt identifier containing metric
        records and aggregate statistics.  If no file exists yet,
        an empty dict is returned.
    """
    if os.path.exists(_DATA_PATH):
        try:
            with open(_DATA_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            # In case of corruption, start fresh rather than crash
            return {}
    return {}


def _save_metrics(data: Dict[str, Any]) -> None:
    """Persist the metrics dictionary to disk as JSON.

    Args:
        data: The metrics dictionary to write.
    """
    os.makedirs(_DATA_DIR, exist_ok=True)
    with open(_DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def record_prompt_metric(prompt_id: str, *args: Any, **kwargs: Any) -> None:
    """Record a new performance datapoint for a prompt.

    This function supports both legacy and enhanced invocation styles.  In
    the legacy form, callers provide named arguments ``rpm``, ``views``,
    ``ctr`` and ``retention`` (optionally using positional order).  In
    the enhanced form, callers provide ``views``, ``clicks``, ``rpm``,
    ``retention`` and an optional ``country_data`` dictionary.  The
    click‑through rate (CTR) will be computed automatically if clicks
    are supplied.  If CTR is provided directly, it is used as‑is.

    Regardless of the call style, this function records a raw snapshot
    in :data:`_RECORDS_PATH` and updates the aggregate statistics in
    the legacy prompt metrics store.  Aggregate values are stored as
    simple averages (not weighted) to maintain backwards compatibility.

    Args:
        prompt_id: Identifier for the prompt (e.g. slug or title).
        *args: Positional arguments supporting the legacy invocation.
        **kwargs: Keyword arguments supporting either invocation style.
            Recognised keys include ``rpm``, ``views``, ``ctr``,
            ``retention``, ``clicks`` and ``country_data``.

    """
    # Initialise variables with None/default values
    rpm: Union[float, None] = None
    views: Union[int, None] = None
    ctr: Union[float, None] = None
    retention: Union[float, None] = None
    clicks: Union[int, None] = None
    country_data: Optional[Dict[str, Any]] = None
    impressions: Union[int, None] = None

    # Extract from keyword arguments first
    if 'rpm' in kwargs:
        rpm = kwargs.pop('rpm')  # type: ignore[assignment]
    if 'views' in kwargs:
        views = kwargs.pop('views')  # type: ignore[assignment]
    if 'ctr' in kwargs:
        ctr = kwargs.pop('ctr')  # type: ignore[assignment]
    if 'retention' in kwargs:
        retention = kwargs.pop('retention')  # type: ignore[assignment]
    if 'clicks' in kwargs:
        clicks = kwargs.pop('clicks')  # type: ignore[assignment]
    if 'impressions' in kwargs:
        impressions = kwargs.pop('impressions')  # type: ignore[assignment]
    if 'country_data' in kwargs:
        country_data = kwargs.pop('country_data')  # type: ignore[assignment]
    # If any unexpected kwargs remain, ignore them

    # Parse positional args based on expected legacy signature.
    # The legacy positional order is (rpm, views, ctr, retention).
    # We only assign if those fields are still None to avoid
    # overriding keyword arguments.
    if args:
        # Use at most four positional args in legacy order
        positional = list(args)
        if rpm is None and len(positional) >= 1:
            rpm = positional[0]  # type: ignore[assignment]
        if views is None and len(positional) >= 2:
            views = positional[1]  # type: ignore[assignment]
        if ctr is None and len(positional) >= 3:
            ctr = positional[2]  # type: ignore[assignment]
        if retention is None and len(positional) >= 4:
            retention = positional[3]  # type: ignore[assignment]
        # Note: additional positional args beyond four are ignored

    # Derive CTR if not provided directly.  If clicks and views are
    # available, compute clicks / views.  If impressions and clicks
    # are provided (rare), compute clicks / impressions.  Otherwise
    # default to zero.  CTR is stored as a fraction (0–1).
    if ctr is None:
        if clicks is not None and views is not None and views > 0:
            ctr = clicks / views
        elif impressions is not None and clicks is not None and impressions > 0:
            ctr = clicks / impressions
        else:
            ctr = 0.0
    # Derive clicks if not provided but CTR and views are known
    if clicks is None and ctr is not None and views is not None:
        # Use round to nearest integer for click count
        clicks = int(round(ctr * views))

    # Default missing numeric values to zero
    rpm = float(rpm) if rpm is not None else 0.0
    views = int(views) if views is not None else 0
    retention = float(retention) if retention is not None else 0.0
    ctr = float(ctr) if ctr is not None else 0.0

    # ------------------------------------------------------------------
    # Persist raw record snapshot
    # ------------------------------------------------------------------
    from datetime import datetime
    record: Dict[str, Any] = {
        "prompt_id": prompt_id,
        "timestamp": datetime.utcnow().isoformat(),
        "views": views,
        "clicks": clicks,
        # store CTR as a fraction (0–1)
        "CTR": ctr,
        "RPM": rpm,
        "retention": retention,
    }
    if country_data:
        record["country_metrics"] = country_data
    # Append to the records file
    existing_records = _load_records(_RECORDS_PATH)
    existing_records.append(record)
    _save_records(existing_records, _RECORDS_PATH)

    # ------------------------------------------------------------------
    # Update legacy aggregate metrics store.  Retain previous behaviour
    # for compatibility with callers expecting avg_rpm, avg_ctr, etc.
    # ------------------------------------------------------------------
    data = _load_metrics()
    metrics = data.get(prompt_id, {"records": []})
    # Append the new record for aggregation (legacy fields only)
    metrics["records"].append(
        {
            "timestamp": time.time(),
            "rpm": rpm,
            "views": views,
            "ctr": ctr,
            "retention": retention,
        }
    )
    # Recompute aggregate statistics as simple averages
    records = metrics["records"]
    if records:
        total_rpm = sum(r["rpm"] for r in records)
        total_views = sum(r["views"] for r in records)
        total_ctr_sum = sum(r["ctr"] for r in records)
        total_ret_sum = sum(r["retention"] for r in records)
        n = len(records)
        metrics["avg_rpm"] = total_rpm / n
        metrics["avg_views"] = total_views / n
        metrics["avg_ctr"] = total_ctr_sum / n
        metrics["avg_retention"] = total_ret_sum / n
    # Save back to disk
    data[prompt_id] = metrics
    _save_metrics(data)


def get_leaderboard(metric: str = 'avg_rpm', top_n: int = 10) -> List[Tuple[str, Dict[str, Any]]]:
    """Return a leaderboard of prompts sorted by a chosen metric.

    Args:
        metric: Which aggregate field to sort by (e.g. 'avg_rpm', 'avg_ctr').
        top_n: Number of top items to return.

    Returns:
        A list of tuples ``(prompt_id, metrics)`` sorted in descending
        order of the requested metric.  If the metric is not present
        for a prompt, a value of 0 is assumed.
    """
    data = _load_metrics()
    # Sort prompts by the specified metric in descending order
    sorted_items = sorted(
        data.items(), key=lambda kv: kv[1].get(metric, 0.0), reverse=True
    )
    return sorted_items[:top_n]


def retire_underperforming(metric: str = 'avg_rpm', threshold: float = 1.0) -> List[str]:
    """Identify prompts whose performance falls below a threshold.

    Args:
        metric: Aggregate metric to evaluate (e.g. 'avg_rpm').
        threshold: Minimum acceptable value.  Prompts with
            ``metric`` below this value are considered underperformers.

    Returns:
        A list of prompt identifiers that should be retired or revised.
    """
    data = _load_metrics()
    return [pid for pid, metrics in data.items() if metrics.get(metric, 0.0) < threshold]


def get_heatmap_by_country(metric: str = 'avg_views') -> Dict[str, float]:
    """Expose a country heatmap of platform metrics via the prompt metrics module.

    This convenience wrapper delegates to the platform metrics module to
    compute a heatmap of the specified metric aggregated by country.  It
    allows callers that import :mod:`prompt_metrics` to access country
    breakdowns without directly referencing :mod:`nova.platform_metrics`.

    Args:
        metric: Which aggregate metric to accumulate by country (default
            ``'avg_views'``).

    Returns:
        A dictionary mapping country codes to aggregated metric values.
    """
    try:
        from nova.platform_metrics import get_country_heatmap  # type: ignore
    except Exception:
        return {}
    return get_country_heatmap(metric=metric)


# ---------------------------------------------------------------------------
# Enhanced analytics functions
#
# The following functions operate on the raw record store created by
# :func:`record_prompt_metric`.  They provide aggregate statistics across
# all prompts, leaderboards and underperformer detection, as well as
# country-level aggregations.  These helpers enable data-driven
# governance decisions without altering the legacy API.  All functions
# accept an optional filepath parameter to support testing with a
# temporary metrics store.
# ---------------------------------------------------------------------------

def get_aggregate_metrics(filepath: Optional[str] = None) -> Dict[str, float]:
    """Compute aggregate metrics across all recorded prompts.

    Args:
        filepath: Path to the records file to load.  If ``None`` (the
            default) the module's :data:`_RECORDS_PATH` is used.  This
            allows tests to override the storage path by monkeypatching
            the module variable.

    Returns:
        A dictionary containing overall statistics: ``total_prompts``
        (number of unique prompt IDs), ``total_views`` (sum of views
        across all records), ``avg_CTR`` (mean click‑through rate),
        ``avg_RPM`` (mean revenue per thousand views) and
        ``avg_retention`` (mean retention value).  If no records exist,
        an empty dictionary is returned.
    """
    path = filepath if filepath is not None else _RECORDS_PATH
    records = _load_records(path)
    if not records:
        return {}
    total_views = 0
    total_ctr = 0.0
    total_rpm = 0.0
    total_ret = 0.0
    for rec in records:
        total_views += int(rec.get('views', 0))
        total_ctr += float(rec.get('CTR', 0.0))
        total_rpm += float(rec.get('RPM', 0.0))
        total_ret += float(rec.get('retention', 0.0))
    n = len(records)
    unique_prompts = {rec.get('prompt_id') for rec in records}
    return {
        'total_prompts': len(unique_prompts),
        'total_views': total_views,
        'avg_CTR': total_ctr / n,
        'avg_RPM': total_rpm / n,
        'avg_retention': total_ret / n,
    }


def get_top_prompts(metric: str, top_n: int = 5, filepath: Optional[str] = None) -> List[Tuple[str, float]]:
    """Return the top prompts sorted by the specified metric.

    The metric name is case-insensitive and may be one of ``'RPM'``,
    ``'CTR'``, ``'views'`` or ``'retention'``.  For each prompt, the
    average of the metric across all its records is computed.  The
    prompts are then sorted in descending order of this average.

    Args:
        metric: Name of the metric to rank by.
        top_n: Number of top prompts to return.
        filepath: Path to the records file.  Defaults to
            :data:`_RECORDS_PATH`.

    Returns:
        A list of ``(prompt_id, value)`` tuples sorted by the chosen
        metric.  If no records exist, an empty list is returned.
    """
    path = filepath if filepath is not None else _RECORDS_PATH
    records = _load_records(path)
    if not records:
        return []
    metric_key = metric.strip().lower()
    # Map common aliases to stored field names
    field_map = {
        'rpm': 'RPM',
        'views': 'views',
        'ctr': 'CTR',
        'retention': 'retention',
    }
    if metric_key not in field_map:
        raise ValueError(f"Unknown metric '{metric}'. Must be one of RPM, CTR, views or retention.")
    field = field_map[metric_key]
    # Aggregate values per prompt
    sums: Dict[str, float] = {}
    counts: Dict[str, int] = {}
    for rec in records:
        pid = rec.get('prompt_id')
        val = rec.get(field)
        if pid is None or val is None:
            continue
        sums[pid] = sums.get(pid, 0.0) + float(val)
        counts[pid] = counts.get(pid, 0) + 1
    # Compute averages per prompt
    averages: List[Tuple[str, float]] = []
    for pid, total in sums.items():
        cnt = counts.get(pid, 1)
        averages.append((pid, total / cnt))
    # Sort descending and return top N
    return sorted(averages, key=lambda kv: kv[1], reverse=True)[:top_n]


def get_underperforming_prompts(metric: str, threshold: float, filepath: Optional[str] = None) -> List[str]:
    """Identify prompts whose average metric is below a threshold.

    Args:
        metric: Name of the metric to evaluate (see
            :func:`get_top_prompts` for valid values).
        threshold: Prompts with averages strictly below this value are
            returned.
        filepath: Path to the records file.  Defaults to
            :data:`_RECORDS_PATH`.

    Returns:
        A list of prompt identifiers considered underperforming.
    """
    top = get_top_prompts(metric, top_n=10_000, filepath=filepath)
    # Filter those below threshold
    under: List[str] = [pid for pid, avg in top if avg < threshold]
    return under


def aggregate_by_country(metric: str, filepath: Optional[str] = None) -> Dict[str, float]:
    """Aggregate a metric across all records, grouped by country.

    The input metric may be one of ``'views'``, ``'RPM'``, ``'CTR'``
    or ``'retention'`` (case-insensitive).  If the metric is a count
    (``views`` or ``clicks``), the values for each country are summed.
    If the metric is a rate (``RPM``, ``CTR`` or ``retention``), the
    average across all records for that country is computed.  Records
    without country information are ignored.

    Args:
        metric: Name of the metric to aggregate by country.
        filepath: Path to the records file.  Defaults to
            :data:`_RECORDS_PATH`.

    Returns:
        A mapping from ISO country codes to aggregated metric values.
    """
    path = filepath if filepath is not None else _RECORDS_PATH
    records = _load_records(path)
    if not records:
        return {}
    metric_key = metric.strip().lower()
    # Determine if metric is a rate or count
    is_rate = metric_key in {'rpm', 'ctr', 'retention'}
    # Prepare accumulators
    totals: Dict[str, float] = {}
    counts: Dict[str, int] = {}
    for rec in records:
        cm = rec.get('country_metrics')
        if not isinstance(cm, dict):
            continue
        for country, metrics in cm.items():
            try:
                # Some country metrics may store RPM under different keys
                # (e.g. 'RPM' vs 'rpm'); normalise case.
                # Also allow lowercase keys in nested metrics.
                country_val = None
                if metric_key == 'views':
                    country_val = metrics.get('views') or metrics.get('view')
                elif metric_key == 'rpm':
                    country_val = metrics.get('RPM') or metrics.get('rpm')
                elif metric_key == 'ctr':
                    country_val = metrics.get('CTR') or metrics.get('ctr')
                elif metric_key == 'retention':
                    country_val = metrics.get('retention')
                if country_val is None:
                    continue
                val = float(country_val)
            except Exception:
                continue
            if is_rate:
                totals[country] = totals.get(country, 0.0) + val
                counts[country] = counts.get(country, 0) + 1
            else:
                # Count metrics are summed
                totals[country] = totals.get(country, 0.0) + val
    # Compute averages for rate metrics
    if is_rate:
        for country in list(totals.keys()):
            cnt = counts.get(country, 1)
            totals[country] = totals[country] / cnt
    return totals