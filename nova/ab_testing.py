"""
A/B testing utilities for Nova Agent.

This module defines a simple manager for running A/B tests across
different aspects of the content pipeline (e.g. thumbnails, prompts,
captions).  It allows operators to define tests with multiple
variants, randomly serve variants to users, record results, and
retrieve performance metrics.  All data is persisted to JSON files
under an ``ab_tests`` directory so that tests survive process
restarts.  Because Nova primarily operates in a backend context,
the manager provides synchronous functions rather than async ones.

Example usage::

    from nova.ab_testing import ABTestManager

    manager = ABTestManager()
    manager.create_test('thumbnail_test', ['thumbA.jpg', 'thumbB.jpg'])
    variant = manager.choose_variant('thumbnail_test')
    # present the chosen thumbnail to the user, then later
    manager.record_result('thumbnail_test', variant, metric=0.42)
    best = manager.best_variant('thumbnail_test')
    print(f'Best performing variant is {best}')

Notes:
    * This manager persists logs and results to disk.  For high
      throughput scenarios consider using a database or cache.
    * Metrics are assumed to be numeric values where higher is better
      (e.g. CTR, RPM).  When computing the best variant the manager
      calculates the average metric per variant.
    * The random selection uses Python's ``random`` module.  For
      reproducibility in tests you may wish to set a seed.
"""

from __future__ import annotations

import json
import os
import random
from datetime import timezone,  datetime
from typing import Any, Dict, List


class ABTestManager:
    """Manage multiple A/B tests and persist their state."""

    def __init__(self, storage_dir: str = "ab_tests") -> None:
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)
        # In-memory cache of tests to avoid repeated disk reads
        self._tests: Dict[str, Dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Persistence helpers
    #
    def _load_test(self, test_id: str) -> Dict[str, Any]:
        """Load a test definition and logs from disk into memory."""
        if test_id in self._tests:
            return self._tests[test_id]
        path = os.path.join(self.storage_dir, f"{test_id}.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data: Dict[str, Any] = json.load(f)
        else:
            data = {}
        self._tests[test_id] = data
        return data

    def _save_test(self, test_id: str, data: Dict[str, Any]) -> None:
        """Persist a test definition and logs to disk."""
        path = os.path.join(self.storage_dir, f"{test_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        # update in-memory cache
        self._tests[test_id] = data

    # ------------------------------------------------------------------
    # Test lifecycle management
    #
    def create_test(self, test_id: str, variants: List[Any]) -> None:
        """Create a new A/B test with the given variants.

        Args:
            test_id: Unique identifier for the test (e.g. 'thumbnail_test').
            variants: A list of variant values (strings, URLs, etc.).

        Raises:
            ValueError: If the test already exists or if fewer than
                two variants are provided.
        """
        if len(variants) < 2:
            raise ValueError("At least two variants are required for an A/B test")
        existing = self._load_test(test_id)
        if existing:
            raise ValueError(f"Test '{test_id}' already exists")
        data = {
            "variants": variants,
            "serving_log": [],  # log of variant selections
            "results": [],      # log of results {variant, metric}
        }
        self._save_test(test_id, data)

    def delete_test(self, test_id: str) -> None:
        """Delete an existing test and its persisted data."""
        self._tests.pop(test_id, None)
        path = os.path.join(self.storage_dir, f"{test_id}.json")
        try:
            os.remove(path)
        except FileNotFoundError:
            pass

    # ------------------------------------------------------------------
    # Variant selection and result recording
    #
    def choose_variant(self, test_id: str) -> Any:
        """Randomly choose and return a variant for a given test.

        Records the choice with a timestamp in the serving log.

        Args:
            test_id: The identifier of the test.

        Returns:
            The selected variant.

        Raises:
            KeyError: If the test has not been created.
        """
        data = self._load_test(test_id)
        variants = data.get("variants")
        if not variants:
            raise KeyError(f"Test '{test_id}' does not exist")
        variant = random.choice(variants)
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "variant": variant,
        }
        data.setdefault("serving_log", []).append(log_entry)
        self._save_test(test_id, data)
        return variant

    def record_result(self, test_id: str, variant: Any, metric: float) -> None:
        """Record the outcome of serving a variant.

        Args:
            test_id: The identifier of the test.
            variant: The variant that was served.
            metric: A numeric performance metric (e.g. CTR, RPM).

        Raises:
            KeyError: If the test or variant does not exist.
        """
        data = self._load_test(test_id)
        variants = data.get("variants")
        if not variants:
            raise KeyError(f"Test '{test_id}' does not exist")
        if variant not in variants:
            raise KeyError(f"Variant '{variant}' is not part of test '{test_id}'")
        result_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "variant": variant,
            "metric": metric,
        }
        data.setdefault("results", []).append(result_entry)
        self._save_test(test_id, data)

    # ------------------------------------------------------------------
    # Reporting
    #
    def get_test(self, test_id: str) -> Dict[str, Any]:
        """Return the full state of a test including logs and results."""
        data = self._load_test(test_id)
        if not data:
            raise KeyError(f"Test '{test_id}' does not exist")
        return data

    def best_variant(self, test_id: str) -> Any:
        """Return the variant with the highest average metric.

        If a variant has no recorded results yet, its average metric is
        considered 0.  If multiple variants tie for the highest
        average, one of them is returned arbitrarily.
        """
        data = self.get_test(test_id)
        results = data.get("results", [])
        if not results:
            # If no results recorded yet, return a random variant
            return random.choice(data["variants"])
        sums: Dict[Any, float] = {v: 0.0 for v in data["variants"]}
        counts: Dict[Any, int] = {v: 0 for v in data["variants"]}
        for r in results:
            variant = r["variant"]
            metric = r.get("metric", 0.0)
            sums[variant] += metric
            counts[variant] += 1
        averages = {v: (sums[v] / counts[v] if counts[v] else 0.0) for v in data["variants"]}
        # Return variant with highest average metric
        return max(averages.items(), key=lambda item: item[1])[0]