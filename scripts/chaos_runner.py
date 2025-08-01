import asyncio, httpx, os, time
from nova.chaos.injector import ChaosConfig, maybe_fail

API = os.getenv("NOVA_API_URL", "http://localhost:8000/health")
SECONDS = int(os.getenv("CHAOS_DURATION_SEC", "60"))
cfg = ChaosConfig(fail_rate=float(os.getenv("CHAOS_FAIL_RATE", "0.2")))

async def main():
    stop = time.time() + SECONDS
    async with httpx.AsyncClient() as client:
        while time.time() < stop:
            try:
                await maybe_fail(cfg)
                r = await client.get(API, timeout=2)
                print("OK" if r.status_code == 200 else f"FAIL {r.status_code}")
            except Exception as e:
                print("Injected/HTTP Error:", e)
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
