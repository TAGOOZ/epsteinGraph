import time


class RateLimiter:
    def __init__(self, min_interval_seconds: float) -> None:
        self.min_interval = max(0.0, min_interval_seconds)
        self._last_time = 0.0

    def wait(self) -> None:
        if self.min_interval <= 0:
            return
        now = time.monotonic()
        elapsed = now - self._last_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self._last_time = time.monotonic()
