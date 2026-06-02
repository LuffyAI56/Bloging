import time
from collections import defaultdict, deque
from threading import Lock


class RateLimiter:
    def __init__(self):
        self._buckets = defaultdict(deque)
        self._last_seen = {}
        self._lock = Lock()
        self._max_keys = 10000
        self._max_age_seconds = 60 * 60

    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        now = time.monotonic()
        with self._lock:
            bucket = self._buckets[key]
            self._last_seen[key] = now
            while bucket and bucket[0] <= now - window_seconds:
                bucket.popleft()
            if len(bucket) >= limit:
                self._cleanup(now)
                return False
            bucket.append(now)
            self._cleanup(now)
            return True

    def clear(self, key: str) -> None:
        with self._lock:
            self._buckets.pop(key, None)
            self._last_seen.pop(key, None)

    def _cleanup(self, now: float) -> None:
        if len(self._last_seen) <= self._max_keys:
            return
        cutoff = now - self._max_age_seconds
        stale_keys = [key for key, last in self._last_seen.items() if last < cutoff]
        for key in stale_keys:
            self._buckets.pop(key, None)
            self._last_seen.pop(key, None)


otp_rate_limiter = RateLimiter()
