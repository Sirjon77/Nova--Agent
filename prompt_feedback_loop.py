
"""Prompt feedback loop.

This module encapsulates logic for adapting prompts based on
historical performance data.  It leverages the ``prompt_metrics``
module to determine which prompts are underperforming and emits
recommendations for revision or retirement.  In a future
iteration, this function could automatically generate new
variations of the retired prompts using the prompt generation
pipeline, perform A/B tests on those variations and schedule
winning prompts for publication.
"""

from __future__ import annotations

import random
from typing import Iterable

from prompt_metrics import get_leaderboard, retire_underperforming


def adapt_prompts(threshold: float = 1.0) -> None:
    """Adapt prompts by examining performance data.

    This function inspects the stored prompt metrics and reports
    which prompts are performing below the given RPM threshold.  It
    prints a summary of top performers and underperformers to
    standard output.  For now, it does not automatically modify
    prompts but highlights where human or automated intervention
    may be required.

    Args:
        threshold: Minimum average RPM; prompts below this are
            considered underperforming.
    """
    # Show a leaderboard of the top 5 prompts by average RPM
    leaderboard = get_leaderboard(metric='avg_rpm', top_n=5)
    if leaderboard:
        print("[prompt_feedback] Top prompts by RPM:")
        for pid, metrics in leaderboard:
            print(f"  {pid}: RPM={metrics.get('avg_rpm', 0):.2f}, CTR={metrics.get('avg_ctr', 0):.3f}, retention={metrics.get('avg_retention', 0):.2f}")
    else:
        print("[prompt_feedback] No prompt metrics found. Run some campaigns first.")

    # Determine underperformers
    underperforming = retire_underperforming(metric='avg_rpm', threshold=threshold)
    if underperforming:
        print("[prompt_feedback] The following prompts are underperforming and should be reviewed or retired:")
        for pid in underperforming:
            print(f"  - {pid}")
    else:
        print("[prompt_feedback] No prompts fall below the RPM threshold.")

