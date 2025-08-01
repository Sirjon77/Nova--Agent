"""Test the TrendScanner's YouTube trending integration.

This unit test verifies that when the TrendScanner is configured with
``use_youtube=True``, it invokes the TubeBuddy/YouTube Data API helper to
retrieve trending videos and incorporates them into the returned trends
list. The test uses monkeypatching to inject a fake trending result.
"""

import asyncio
import unittest
from unittest.mock import patch

import os
import sys

# Append package root so that modules can be imported when running tests
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(base_dir)

from nova.governance.trend_scanner import TrendScanner


class TestTrendScannerYouTube(unittest.TestCase):
    """Tests for YouTube trending in TrendScanner."""

    def test_youtube_trending_integration(self) -> None:
        # Configure the scanner to use YouTube trending
        cfg = {
            "rpm_multiplier": 2,
            "top_n": 10,
            "use_youtube": True,
            "use_tiktok": False,
            "use_vidiq": False,
        }
        scanner = TrendScanner(cfg)

        # Prepare a fake trending list with two videos
        fake_videos = [
            {"title": "Test Video 1", "id": "v1", "description": "d", "channelTitle": "ch"},
            {"title": "Test Video 2", "id": "v2", "description": "d2", "channelTitle": "ch2"},
        ]

        async def run_scan():
            # Patch get_trending_videos to return fake_videos
            with patch("integrations.tubebuddy.get_trending_videos", return_value=fake_videos):
                results = await scanner.scan(["seed"])
                return results

        # Execute the async scan
        results = asyncio.get_event_loop().run_until_complete(run_scan())

        # There should be at least three results: one from the seed and two from YouTube
        self.assertGreaterEqual(len(results), 3)
        # Filter for youtube_trending source
        yt_results = [r for r in results if r.get("source") == "youtube_trending"]
        self.assertEqual(len(yt_results), 2)
        # Ensure projected RPM uses rpm_multiplier
        for r in yt_results:
            self.assertEqual(r["interest"], 1.0)
            self.assertEqual(r["projected_rpm"], 1.0 * cfg["rpm_multiplier"])


if __name__ == "__main__":
    unittest.main()