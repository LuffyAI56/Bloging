import time
from collections import defaultdict, deque
from threading import Lock


class RateLimiter:
    def __init__(self):
        self._buckets = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        now = time.monotonic()
        with self._lock:
            bucket = self._buckets[key]
            while bucket and bucket[0] <= now - window_seconds:
                bucket.popleft()
            if len(bucket) >= limit:
                return False
            bucket.append(now)
            return True

    def clear(self, key: str) -> None:
        with self._lock:
            self._buckets.pop(key, None)


otp_rate_limiter = RateLimiter()
