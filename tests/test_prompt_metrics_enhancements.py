"""Tests for the enhanced prompt_metrics module.

These tests exercise the new functionality added to ``prompt_metrics.py``
including raw record persistence, aggregate calculations, leaderboards,
underperformance detection and country-level aggregation.  They also
verify that legacy invocation of :func:`record_prompt_metric` still
works as expected.  All tests use temporary file paths to avoid
touching the real metrics store in the repository.
"""

from __future__ import annotations

import os
import json
import types
import importlib
from typing import Any, Dict, List

import pytest


@pytest.fixture(autouse=True)
def isolate_metrics(tmp_path, monkeypatch):
    """Redirect the prompt metrics storage to a temporary directory.

    This fixture automatically runs for each test.  It patches
    ``prompt_metrics._RECORDS_PATH`` and ``prompt_metrics._DATA_PATH``
    to point to files under a provided temporary directory.  At the end
    of each test the original paths are restored.
    """
    import prompt_metrics as pm
    # Save original values
    orig_records = pm._RECORDS_PATH
    orig_data = pm._DATA_PATH
    # Point to temporary files
    records_file = tmp_path / "records.json"
    data_file = tmp_path / "aggregated.json"
    monkeypatch.setattr(pm, "_RECORDS_PATH", str(records_file), raising=False)
    monkeypatch.setattr(pm, "_DATA_PATH", str(data_file), raising=False)
    yield
    # Restore original values (monkeypatch will undo on teardown)


def test_record_and_load_metrics():
    import prompt_metrics as pm
    # Record a new metric using enhanced parameters
    pm.record_prompt_metric(
        "test_prompt",
        views=1000,
        clicks=100,
        rpm=5.0,
        retention=50.0,
        country_data={
            "US": {"views": 800, "RPM": 6.0},
            "IN": {"views": 200, "RPM": 4.0},
        },
    )
    # Load records and verify contents
    recs = pm.load_metrics()
    assert len(recs) == 1
    rec = recs[0]
    assert rec["prompt_id"] == "test_prompt"
    assert rec["views"] == 1000
    # CTR should be clicks/views = 0.1
    assert abs(rec["CTR"] - 0.1) < 1e-6
    assert rec["RPM"] == 5.0
    assert rec["retention"] == 50.0
    assert "country_metrics" in rec and "US" in rec["country_metrics"]


def test_aggregate_metrics():
    import prompt_metrics as pm
    # Two prompts with known values
    pm.record_prompt_metric("p1", views=1000, clicks=100, rpm=5.0, retention=50.0)
    pm.record_prompt_metric("p2", views=500, clicks=25, rpm=10.0, retention=40.0)
    agg = pm.get_aggregate_metrics()
    # Two unique prompts
    assert agg["total_prompts"] == 2
    # Total views = 1500
    assert agg["total_views"] == 1500
    # CTR: (0.1 + 0.05) / 2
    assert abs(agg["avg_CTR"] - 0.075) < 1e-6
    # RPM: (5 + 10) / 2
    assert abs(agg["avg_RPM"] - 7.5) < 1e-6
    # Retention: (50 + 40) / 2
    assert abs(agg["avg_retention"] - 45.0) < 1e-6


def test_get_top_prompts():
    import prompt_metrics as pm
    # Add three prompts with varying RPMs
    pm.record_prompt_metric("a", views=100, clicks=10, rpm=2.0, retention=10.0)
    pm.record_prompt_metric("b", views=100, clicks=20, rpm=5.0, retention=20.0)
    pm.record_prompt_metric("c", views=100, clicks=30, rpm=8.0, retention=30.0)
    top = pm.get_top_prompts("RPM", top_n=2)
    # Expect prompts c (8.0) and b (5.0) in that order
    assert top[0][0] == "c"
    assert abs(top[0][1] - 8.0) < 1e-6
    assert top[1][0] == "b"
    assert abs(top[1][1] - 5.0) < 1e-6


def test_get_underperforming_prompts():
    import prompt_metrics as pm
    # Add three prompts
    pm.record_prompt_metric("x", views=100, clicks=50, rpm=1.0, retention=10.0)
    pm.record_prompt_metric("y", views=100, clicks=10, rpm=3.0, retention=20.0)
    pm.record_prompt_metric("z", views=100, clicks=5, rpm=5.0, retention=30.0)
    # Underperformers by RPM with threshold=4.0 should include x and y
    under = pm.get_underperforming_prompts("RPM", threshold=4.0)
    assert set(under) == {"x", "y"}


def test_aggregate_by_country():
    import prompt_metrics as pm
    # Record two prompts with country breakdowns
    pm.record_prompt_metric(
        "p1",
        views=100,
        clicks=10,
        rpm=4.0,
        retention=10.0,
        country_data={"US": {"views": 60, "RPM": 5.0}, "CA": {"views": 40, "RPM": 3.0}},
    )
    pm.record_prompt_metric(
        "p2",
        views=100,
        clicks=20,
        rpm=6.0,
        retention=20.0,
        country_data={"US": {"views": 30, "RPM": 7.0}, "UK": {"views": 70, "RPM": 2.0}},
    )
    # Aggregate view counts per country
    views_heat = pm.aggregate_by_country("views")
    assert views_heat["US"] == 90  # 60 + 30
    assert views_heat["CA"] == 40
    assert views_heat["UK"] == 70
    # Aggregate RPM averages per country
    rpm_heat = pm.aggregate_by_country("RPM")
    # US RPM average: (5.0 + 7.0)/2 = 6.0
    assert abs(rpm_heat["US"] - 6.0) < 1e-6
    # CA RPM average: 3.0
    assert abs(rpm_heat["CA"] - 3.0) < 1e-6
    # UK RPM average: 2.0
    assert abs(rpm_heat["UK"] - 2.0) < 1e-6


def test_legacy_invocation():
    import prompt_metrics as pm
    # Legacy call: rpm, views, ctr, retention
    pm.record_prompt_metric("legacy", 10.0, 1000, 0.02, 0.4)
    recs = pm.load_metrics()
    # Should record one entry with CTR equal to provided value
    assert len(recs) == 1
    rec = recs[0]
    assert rec["prompt_id"] == "legacy"
    assert rec["views"] == 1000
    # CTR stored as fraction (0.02)
    assert abs(rec["CTR"] - 0.02) < 1e-6
    # Clicks should be derived: 0.02 * 1000 = 20
    assert rec["clicks"] == 20