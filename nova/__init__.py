"""Nova package initialisation.

This module exposes commonly used metrics counters while avoiding
heavy imports that may depend on configuration files.  The original
implementation imported the ``governance`` submodule unconditionally,
which in turn loaded configuration from disk at import time.  If
configuration files were missing, this caused a FileNotFoundError on
import.  To make the package more robust, we attempt to import
``governance`` inside a try/except block and fall back to ``None`` if
the import fails.
"""

try:
    import governance  # type: ignore
except Exception:
    # If governance import fails (e.g. missing config), leave it as None
    governance = None  # type: ignore

from .metrics import tasks_executed, task_duration, memory_items  # noqa: F401