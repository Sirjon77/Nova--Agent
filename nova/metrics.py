"""Prometheus metrics exporter for Nova Agent v6.5.

This module exposes counters, histograms and gauges used throughout
Nova Agent to track task execution and governance cycles. Duplicate
definitions and stray newline markers have been removed for clarity.
"""

from prometheus_client import Counter, Histogram, Gauge

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
