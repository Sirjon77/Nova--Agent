import pathlib
import yaml
import logging
import psutil
import os
from typing import Union

log = logging.getLogger("Policy")

class PolicyEnforcer:
    def __init__(self, path: Union[str, pathlib.Path] = 'config/policy.yaml'):
        self.path = pathlib.Path(path)
        if not self.path.exists():
            log.warning("Policy file %s not found, using empty policy", self.path)
            self._policy = {}
        else:
            with self.path.open() as f:
                self._policy = yaml.safe_load(f) or {}

    # --- Tool checks ----------------------------------------------------
    def tool_allowed(self, tool_name: str) -> bool:
        allowed = set(self._policy.get('sandbox', {}).get('allowed_tools', []))
        return not allowed or tool_name in allowed

    def enforce_tool(self, tool_name: str):
        if not self.tool_allowed(tool_name):
            raise PermissionError(f"Tool {tool_name} is blocked by policy")

    # --- Memory checks --------------------------------------------------
    def check_memory(self):
        limit = self._policy.get('sandbox', {}).get('memory_limit_mb')
        if not limit:
            return True
        usage = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
        return usage <= limit
