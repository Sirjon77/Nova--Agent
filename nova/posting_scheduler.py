"""Posting Scheduler Module.

This module defines a simple scheduler that suggests optimal posting
times based on platform-specific heuristics and local time zones.
The ``PostingScheduler`` class can be used to compute a posting
calendar for the week and adjust timing to maximise engagement and
RPM.  In a production environment, this would likely integrate
with analytics services like Metricool or ViralStat to use actual
engagement data.
"""

from __future__ import annotations

from datetime import datetime, timedelta, time
from typing import List


class PostingScheduler:
    """Computes optimal posting times for social media content."""

    # Default posting windows by platform (local time).  These are
    # heuristics based on common engagement patterns.
    DEFAULT_WINDOWS = {
        "tiktok": [(time(18, 0), time(21, 0))],
        "youtube": [(time(18, 0), time(21, 0))],
        "instagram": [(time(19, 0), time(22, 0))],
        "facebook": [(time(19, 0), time(22, 0))],
    }

    def __init__(self, timezone_offset_hours: int = 0) -> None:
        """Initialise the scheduler with a timezone offset (in hours).

        Args:
            timezone_offset_hours: Difference from UTC for the target region.
        """
        self.offset = timedelta(hours=timezone_offset_hours)

    def compute_post_times(
        self, platform: str, days_ahead: int = 7, posts_per_day: int = 1
    ) -> List[datetime]:
        """Generate a list of posting times.

        Args:
            platform: The platform to schedule for (e.g., 'tiktok').
            days_ahead: Number of days to schedule into the future.
            posts_per_day: How many posts per day.

        Returns:
            A list of datetimes adjusted to the target timezone.
        """
        windows = self.DEFAULT_WINDOWS.get(platform.lower())
        if not windows:
            return []
        now = datetime.utcnow() + self.offset
        schedule: List[datetime] = []
        for day in range(days_ahead):
            day_date = (now + timedelta(days=day)).date()
            for win in windows:
                start, end = win
                # Spread posts evenly within the window
                total_minutes = (datetime.combine(day_date, end) - datetime.combine(day_date, start)).seconds // 60
                interval = total_minutes // max(1, posts_per_day)
                for i in range(posts_per_day):
                    post_time = datetime.combine(
                        day_date,
                        (datetime.min + timedelta(minutes=start.hour * 60 + start.minute + i * interval)).time(),
                    )
                    schedule.append(post_time)
        return schedule
