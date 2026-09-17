"""Simple token-bucket rate limiter for async code."""

from __future__ import annotations

import asyncio
import time
from typing import Optional


class RateLimiter:
    """Token-bucket rate limiter.

    Allows up to `rate` requests per second with a burst capacity.
    """

    def __init__(self, rate: float = 2.0, capacity: Optional[float] = None) -> None:
        self.rate = rate
        self.capacity = capacity if capacity is not None else rate * 2
        self.tokens = self.capacity
        self.updated_at = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: float = 1.0) -> None:
        """Wait until the requested number of tokens is available."""
        async with self._lock:
            while True:
                now = time.monotonic()
                elapsed = now - self.updated_at
                self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
                self.updated_at = now

                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return

                # Wait for the deficit to be refilled
                deficit = tokens - self.tokens
                wait_time = deficit / self.rate
                await asyncio.sleep(wait_time)
