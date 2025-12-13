
from dataclasses import dataclass
import time
import httpx

@dataclass
class ToolConfig:
    name: str
    ping_url: str
    expected_ms: int
    cost_per_call: float

from nova.policy import PolicyEnforcer

class ToolChecker:
    def __init__(self, cfg):
        self.enforcer = PolicyEnforcer()

        self.cfg = cfg

    async def check(self, tool: ToolConfig):
        self.enforcer.enforce_tool(tool.name)
        start = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=5) as c:
                r = await c.get(tool.ping_url)
            latency = (time.perf_counter() - start) * 1000
            status = 'ok' if r.status_code < 400 else 'error'
        except Exception:
            latency = (time.perf_counter() - start) * 1000
            status = 'error'
        score = 50
        score += -10 if latency > tool.expected_ms else 5
        score += -15 if status=='error' else 0
        score += -10 if tool.cost_per_call > self.cfg.get('cost_threshold',0.002) else 0
        return {'tool':tool.name,'latency_ms':int(latency),'status':status,'score':score}
