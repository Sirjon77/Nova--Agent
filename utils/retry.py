import functools, time

def retry(times=3, delay=1.0):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            for i in range(times):
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    if i == times - 1:
                        raise
                    time.sleep(delay)
        return wrapper
    return decorator
