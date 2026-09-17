"""Base spider class."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from scraper.core.client import AsyncScraperClient

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class BaseSpider(ABC, Generic[T]):
    """Abstract base class for all spiders."""

    name: str = "base"

    def __init__(self, client: AsyncScraperClient | None = None, **kwargs: Any) -> None:
        self.client = client
        self.kwargs = kwargs

    @abstractmethod
    async def parse(self, html: str, url: str) -> list[T]:
        """Parse a single page and return a list of items."""

    @abstractmethod
    async def run(self) -> list[T]:
        """Execute the spider and return all collected items."""

    async def _ensure_client(self) -> AsyncScraperClient:
        if self.client is None:
            self.client = AsyncScraperClient()
        return self.client
