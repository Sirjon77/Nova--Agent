import logging, random, asyncio
log = logging.getLogger("ChaosInjector")

class ChaosConfig:
    def __init__(self, fail_rate=0.1, delay_ms=500):
        self.fail_rate = fail_rate
        self.delay_ms = delay_ms

async def maybe_fail(cfg: ChaosConfig):
    # Random latency
    await asyncio.sleep(cfg.delay_ms / 1000.0 * random.random())
    if random.random() < cfg.fail_rate:
        raise RuntimeError("Injected chaos failure")
