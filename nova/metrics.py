"""Prometheus metrics exporter for Nova Agent v6.5.

This module exposes counters, histograms and gauges used throughout
Nova Agent to track task execution and governance cycles. Duplicate
definitions and stray newline markers have been removed for clarity.
"""

from prometheus_client import Counter, Histogram, Gauge, Summary

# Task execution metrics
tasks_executed = Counter(
    "nova_tasks_executed_total",
    "Total tasks executed"
)
task_duration = Histogram(
    "nova_task_duration_seconds",
    "Task execution duration"
)
memory_items = Gauge(
    "nova_memory_items",
    "Items in agent memory store"
)

# Governance metrics
governance_runs_total = Counter(
    "nova_governance_runs_total",
    "Governance cycles"
)

# Number of channels scored per governance cycle
channels_scored = Counter(
    "nova_governance_channels_scored_total",
    "Channels scored in governance loop"
)

# Number of recommendations (actions) flagged per governance cycle
actions_flagged = Counter(
    "nova_governance_actions_flagged_total",
    "Recommendations (actions) flagged in governance loop"
)

# Duration of governance loop execution
governance_loop_duration = Summary(
    "nova_governance_loop_duration_seconds",
    "Duration of governance loop execution"
)

# Channel flag metrics
flagged_channels_total = Counter(
    "nova_flagged_channels_total",
    "Total number of channels flagged by type",
    labelnames=["flag"]
)

# Tool health metrics
tool_health_status = Gauge(
    "nova_tool_health_status",
    "Tool health status (1 ok, 0 error)",
    labelnames=["tool"]
)

tool_latency_ms = Gauge(
    "nova_tool_latency_ms",
    "Tool latency in milliseconds",
    labelnames=["tool"]
)

# Content policy compliance metrics
silent_video_ratio_compliance = Gauge(
    "nova_silent_video_ratio_compliance",
    "Silent video ratio compliance status (1 compliant, 0 non-compliant)",
    labelnames=["channel"]
)

silent_video_ratio_actual = Gauge(
    "nova_silent_video_ratio_actual",
    "Actual silent video ratio for channel",
    labelnames=["channel"]
)

content_posts_processed = Counter(
    "nova_content_posts_processed_total",
    "Total content posts processed by policy engine",
    labelnames=["content_type", "channel"]
)

silent_posts_generated = Counter(
    "nova_silent_posts_generated_total",
    "Total silent posts generated",
    labelnames=["channel", "avatar_included"]
)
