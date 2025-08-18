import pytest
from nova.chaos.injector import ChaosConfig, maybe_fail

@pytest.mark.asyncio
async def test_maybe_fail():
    cfg = ChaosConfig(fail_rate=0.0, delay_ms=10)
    # Should not raise
    await maybe_fail(cfg)
