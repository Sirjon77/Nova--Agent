"""Metrics server setup for Prometheus monitoring."""
import logging
from prometheus_client import start_http_server
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
requests_total = Counter("requests_total", "Total HTTP requests")
request_duration = Histogram("request_duration_seconds", "Request duration in seconds")
active_connections = Gauge("active_connections", "Number of active connections")
memory_usage = Gauge("memory_usage_bytes", "Memory usage in bytes")

def init_metrics_server(port: int = 8000):
    """Initialize the Prometheus metrics server."""
    try:
        start_http_server(port)
        logging.info(f"Metrics server started on port {port}")
    except Exception as e:
        logging.error(f"Failed to start metrics server: {e}")
        raise 