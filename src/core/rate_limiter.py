import time
import asyncio
from collections import defaultdict
from typing import Callable


class RateLimiter:
    """
    Rate limiter para APIs externas.
    Implementa token bucket y sliding window para controlar requests.
    """

    def __init__(self):
        self._buckets: dict[str, dict] = {}
        self._sliding_windows: dict[str, list[float]] = defaultdict(list)

    def add_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: float,
    ):
        self._buckets[key] = {
            "max_requests": max_requests,
            "window_seconds": window_seconds,
            "tokens": max_requests,
            "last_refill": time.monotonic(),
        }

    async def wait_for_token(self, key: str):
        if key not in self._buckets:
            return

        bucket = self._buckets[key]
        while True:
            now = time.monotonic()
            elapsed = now - bucket["last_refill"]

            bucket["tokens"] = min(
                bucket["max_requests"],
                bucket["tokens"] + (elapsed / bucket["window_seconds"]) * bucket["max_requests"],
            )
            bucket["last_refill"] = now

            if bucket["tokens"] >= 1:
                bucket["tokens"] -= 1
                return

            wait_time = (1 - bucket["tokens"]) * bucket["window_seconds"] / bucket["max_requests"]
            await asyncio.sleep(wait_time)

    def is_rate_limited(self, key: str) -> bool:
        if key not in self._buckets:
            return False

        bucket = self._buckets[key]
        now = time.monotonic()
        elapsed = now - bucket["last_refill"]

        bucket["tokens"] = min(
            bucket["max_requests"],
            bucket["tokens"] + (elapsed / bucket["window_seconds"]) * bucket["max_requests"],
        )
        bucket["last_refill"] = now

        if bucket["tokens"] < 1:
            return True

        bucket["tokens"] -= 1
        return False

    def get_remaining(self, key: str) -> int:
        if key not in self._buckets:
            return -1
        return int(self._buckets[key]["tokens"])


rate_limiter = RateLimiter()

rate_limiter.add_rate_limit("predictit", max_requests=1, window_seconds=1.0)
rate_limiter.add_rate_limit("polymarket", max_requests=10, window_seconds=1.0)
rate_limiter.add_rate_limit("kalshi", max_requests=20, window_seconds=1.0)
rate_limiter.add_rate_limit("manifold", max_requests=10, window_seconds=1.0)
rate_limiter.add_rate_limit("hyperliquid", max_requests=30, window_seconds=1.0)
