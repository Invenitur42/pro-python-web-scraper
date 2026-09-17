"""Async HTTP client with retries, rate limiting and user-agent rotation."""

from __future__ import annotations

import asyncio
import logging
import random
from typing import Any, Optional

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from scraper.core.exceptions import RequestError
from scraper.core.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]


class AsyncScraperClient:
    """High-level async HTTP client tailored for scraping."""

    def __init__(
        self,
        *,
        timeout: float = 30.0,
        max_retries: int = 3,
        concurrency: int = 5,
        delay: float = 0.3,
        user_agents: Optional[list[str]] = None,
        proxy: Optional[str] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> None:
        self.timeout = timeout
        self.max_retries = max_retries
        self.concurrency = concurrency
        self.delay = delay
        self.user_agents = user_agents or DEFAULT_USER_AGENTS
        self.proxy = proxy

        self._semaphore = asyncio.Semaphore(concurrency)
        self._rate_limiter = RateLimiter(rate=1.0 / max(delay, 0.05))

        limits = httpx.Limits(max_connections=concurrency * 2, max_keepalive_connections=concurrency)
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            limits=limits,
            proxy=proxy,
            follow_redirects=True,
            headers=headers or {},
            http2=True,
        )

    async def __aenter__(self) -> "AsyncScraperClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def close(self) -> None:
        await self._client.aclose()

    def _random_ua(self) -> str:
        return random.choice(self.user_agents)

    @retry(
        retry=retry_if_exception_type((httpx.TransportError, httpx.TimeoutException)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        headers = kwargs.pop("headers", {})
        headers.setdefault("User-Agent", self._random_ua())
        headers.setdefault("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
        headers.setdefault("Accept-Language", "en-US,en;q=0.9")

        async with self._semaphore:
            await self._rate_limiter.acquire()
            logger.debug("%s %s", method.upper(), url)
            response = await self._client.request(method, url, headers=headers, **kwargs)
            response.raise_for_status()
            return response

    async def get(self, url: str, **kwargs: Any) -> httpx.Response:
        try:
            return await self._request("GET", url, **kwargs)
        except Exception as exc:
            logger.error("Failed to GET %s: %s", url, exc)
            raise RequestError(f"GET {url} failed after retries") from exc

    async def get_text(self, url: str, **kwargs: Any) -> str:
        response = await self.get(url, **kwargs)
        return response.text

    async def get_json(self, url: str, **kwargs: Any) -> Any:
        response = await self.get(url, **kwargs)
        return response.json()
