"""Celery task definitions for Nova.

This module defines asynchronous tasks that can be scheduled or
executed via a Celery worker.  Tasks include posting videos to
multiple platforms using the platform manager and generating
weekly performance digests and landing pages for top prompts.

To enable these tasks, ensure that a Celery worker is running
with the appropriate broker and backend configured in
``celeryconfig.py``.  For example::

    celery -A tasks worker --beat --loglevel=info

The ``beat`` scheduler can be used to automatically trigger
``weekly_digest`` at a regular cadence (e.g. weekly) by adding
an entry to ``celeryconfig.py``.
"""

from __future__ import annotations

try:
    from celery import Celery  # type: ignore
except Exception:
    Celery = None  # type: ignore

from platform_manager import manage_platforms
from marketing_digest import (
    push_weekly_digest_to_notion,
    generate_landing_pages_for_top_prompts,
)
from typing import Union

# If Celery is available, configure the app and register tasks.  If
# Celery is not installed, define stub functions so that imports
# succeed but tasks do nothing.
if Celery is not None:
    app = Celery('nova_tasks')
    app.config_from_object('celeryconfig')

    @app.task(name='nova.post_video')
    def post_video(video_path: str, prompt: str, prompt_id: Union[str, None] = None) -> str:
        """Asynchronous task to post a video across platforms.

        Delegates to ``platform_manager.manage_platforms`` and returns
        the result string.  If any exception occurs during posting,
        it will propagate to the Celery worker and be logged.

        Args:
            video_path: Path to the video file on disk.
            prompt: Textual prompt or title used for the video.
            prompt_id: Optional unique identifier for tracking metrics.

        Returns:
            The summary string returned by ``manage_platforms``.
        """
        return manage_platforms(video_path, prompt, prompt_id)

    @app.task(name='nova.weekly_digest')
    def weekly_digest() -> str:
        """Generate a weekly digest and landing pages.

        This task performs three actions:
          1. Generate and upload the weekly performance digest to
             Notion via ``push_weekly_digest_to_notion``.
          2. Generate micro landing pages for the top prompts and save
             them to the default ``landing_pages`` directory.
          3. Return a success message.

        Note: The Notion upload will only occur if ``NOTION_TOKEN`` and
        ``NOTION_DATABASE_ID`` environment variables are configured.

        Returns:
            A status string indicating completion.
        """
        push_weekly_digest_to_notion()
        generate_landing_pages_for_top_prompts(num_pages=3, output_dir='landing_pages')
        return 'Weekly digest and landing pages generated'

    @app.task(name='nova.competitor_analysis')
    def competitor_analysis(seeds: Union[list[str], None] = None, count: int = 10):
        """Asynchronously benchmark competitor keywords.

        This task invokes the :class:`nova.competitor_analyzer.CompetitorAnalyzer`
        to fetch trending keywords and fabricate performance metrics for
        competitor topics.  The seeds and count can be supplied
        directly or derived from the ``COMPETITOR_SEEDS`` environment
        variable.  Results are returned as a list of dictionaries.

        Args:
            seeds: Optional list of seed keywords.  If omitted, this
                will be parsed from the ``COMPETITOR_SEEDS`` environment
                variable (comma‑separated).  If still empty, an empty
                list is passed to the analyzer.
            count: Maximum number of competitor entries to return.

        Returns:
            A list of competitor benchmarking results.
        """
        import os
        import asyncio
        try:
            from nova.competitor_analyzer import CompetitorAnalyzer  # type: ignore
        except Exception:
            return []
        # Derive seeds from parameter or environment variable
        if seeds is None:
            env = os.getenv('COMPETITOR_SEEDS', '')
            seeds = [s.strip() for s in env.split(',') if s.strip()]
        cfg = {'rpm_multiplier': 1.0, 'top_n': count}
        analyzer = CompetitorAnalyzer(cfg)
        return asyncio.run(analyzer.benchmark_competitors(seeds, count))

    @app.task(name='nova.process_metrics')
    def process_metrics():
        """Aggregate metrics, compute leaderboards and retire underperformers.

        This task uses the platform metrics module to identify prompts
        that fall below the configured RPM threshold and to produce a
        cross‑platform leaderboard.  The threshold can be overridden via
        the ``RETIRE_THRESHOLD`` environment variable.  Returned data
        include the list of retired prompt IDs and the leaderboard.

        Returns:
            A dictionary with keys ``retired`` and ``leaderboard``.
        """
        import os
        try:
            from nova.platform_metrics import retire_underperforming, get_platform_leaderboard  # type: ignore
        except Exception:
            return {'retired': [], 'leaderboard': []}
        try:
            threshold = float(os.getenv('RETIRE_THRESHOLD', '1.0'))
        except Exception:
            threshold = 1.0
        retired = retire_underperforming(metric='avg_rpm', threshold=threshold)
        leaderboard = get_platform_leaderboard(metric='avg_rpm')
        return {'retired': retired, 'leaderboard': leaderboard}

    @app.task(name='nova.suggest_hashtags')
    def suggest_hashtags(topic: str, count: int = 10) -> list[str]:
        """Suggest relevant hashtags for a topic using the hashtag optimiser.

        The task respects the ``HASHTAG_DYNAMIC`` environment variable to
        determine whether to fetch dynamic hashtags.  If dynamic mode
        fails or is disabled, it falls back to the static suggestion
        logic.  Returned hashtags are trimmed to the requested count.

        Args:
            topic: The topic or keyword for which to generate hashtags.
            count: Maximum number of hashtags to return.

        Returns:
            A list of hashtag strings.
        """
        import os
        try:
            from nova.hashtag_optimizer import HashtagOptimizer  # type: ignore
        except Exception:
            return []
        opt = HashtagOptimizer()
        use_dynamic = os.getenv('HASHTAG_DYNAMIC', '').lower() in {'1', 'true', 'yes'}
        try:
            if use_dynamic:
                tags = opt.suggest_dynamic(topic, count=count)
            else:
                tags = opt.suggest(topic, count=count)
        except Exception:
            tags = opt.suggest(topic, count=count)
        return tags[:count]
else:
    # Define no-op stubs for environments without Celery.
    app = None  # type: ignore

    def post_video(video_path: str, prompt: str, prompt_id: Union[str, None] = None) -> str:
        """Synchronous fallback for post_video when Celery is unavailable."""
        return manage_platforms(video_path, prompt, prompt_id)

    def weekly_digest() -> str:
        """Synchronous fallback for weekly_digest when Celery is unavailable."""
        push_weekly_digest_to_notion()
        generate_landing_pages_for_top_prompts(num_pages=3, output_dir='landing_pages')
        return 'Weekly digest and landing pages generated'

    def competitor_analysis(seeds: Union[list[str], None] = None, count: int = 10):
        """Synchronous fallback for competitor_analysis when Celery is unavailable."""
        return []

    def process_metrics():
        """Synchronous fallback for process_metrics when Celery is unavailable."""
        return {'retired': [], 'leaderboard': []}

    def suggest_hashtags(topic: str, count: int = 10) -> list[str]:
        """Synchronous fallback for suggest_hashtags when Celery is unavailable."""
        try:
            from nova.hashtag_optimizer import HashtagOptimizer  # type: ignore
        except Exception:
            return []
        opt = HashtagOptimizer()
        try:
            return opt.suggest(topic, count=count)
        except Exception:
            return []