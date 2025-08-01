
"""Analytics worker that consumes event queue and updates dashboards."""
import time
import logging
from metrics.metrics_setup import init_metrics_server

def main():
    logging.basicConfig(level=logging.INFO)
    init_metrics_server(8000)
    logging.info("Analytics worker started")
    while True:
        # TODO: connect to event store, update RPM dashboards, etc.
        time.sleep(10)

if __name__ == "__main__":
    main()
