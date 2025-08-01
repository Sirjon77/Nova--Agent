
"""Decorator to wrap agent tasks with error catching, logging, and Sentry reporting."""
import functools
import logging
import os

SENTRY_DSN = os.getenv("SENTRY_DSN", "")
_sentry_client = None
if SENTRY_DSN:
    try:
        import sentry_sdk
        sentry_sdk.init(dsn=SENTRY_DSN, traces_sample_rate=0.1)
        _sentry_client = sentry_sdk
    except ImportError:
        logging.warning("sentry-sdk not installed; install it to enable Sentry reporting.")

def safe_run(task_name: str):
    """Wrap any callable so that exceptions are logged and reported but don't kill the worker."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logging.exception("Task %s crashed: %s", task_name, e)
                if _sentry_client:
                    _sentry_client.capture_exception(e)
                # Continue without raising further
        return wrapper
    return decorator
