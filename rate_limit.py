
import time
import redis
from functools import wraps

redis_url = 'redis://redis:6379/0'
r = redis.Redis.from_url(redis_url)

def rate_limited(key: str, limit: int, window: int = 60):
    """Simple counter‑based rate limiter using Redis."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = int(time.time())
            bucket = f"{key}:{now // window}"
            if r.incr(bucket, 1) > limit:
                sleep_time = window - (now % window)
                time.sleep(sleep_time)
            r.expire(bucket, window * 2)
            for attempt in range(5):
                try:
                    return func(*args, **kwargs)
                except Exception:
                    if attempt == 4:
                        raise
                    backoff = 2 ** attempt
                    time.sleep(backoff)
        return wrapper
    return decorator
