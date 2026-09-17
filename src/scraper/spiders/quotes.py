"""Spider for https://quotes.toscrape.com – classic demo target."""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from scraper.core.client import AsyncScraperClient
from scraper.models.quote import Quote
from scraper.spiders.base import BaseSpider

logger = logging.getLogger(__name__)


class QuotesSpider(BaseSpider[Quote]):
    name = "quotes"
    base_url = "https://quotes.toscrape.com"

    def __init__(
        self,
        max_pages: int = 5,
        client: AsyncScraperClient | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(client=client, **kwargs)
        self.max_pages = max_pages

    async def parse(self, html: str, url: str) -> list[Quote]:
        soup = BeautifulSoup(html, "lxml")
        items: list[Quote] = []

        for quote_div in soup.select("div.quote"):
            text = quote_div.select_one("span.text")
            author = quote_div.select_one("small.author")
            tags = [t.get_text(strip=True) for t in quote_div.select("div.tags a.tag")]
            author_link = quote_div.select_one("span a")

            if not text or not author:
                continue

            author_url = None
            if author_link and author_link.get("href"):
                author_url = urljoin(self.base_url, author_link["href"])

            try:
                item = Quote(
                    text=text.get_text(strip=True).strip("“”\""),
                    author=author.get_text(strip=True),
                    tags=tags,
                    author_url=author_url,
                )
                items.append(item)
            except Exception as exc:
                logger.warning("Failed to parse quote on %s: %s", url, exc)

        return items

    async def run(self) -> list[Quote]:
        client = await self._ensure_client()
        all_items: list[Quote] = []

        async with client:
            for page in range(1, self.max_pages + 1):
                url = f"{self.base_url}/page/{page}/" if page > 1 else self.base_url
                logger.info("Scraping page %d: %s", page, url)

                try:
                    html = await client.get_text(url)
                    items = await self.parse(html, url)
                    all_items.extend(items)
                    logger.info("  → extracted %d quotes", len(items))

                    # Stop early if the page returned no quotes (end of pagination)
                    if not items:
                        logger.info("No more quotes found, stopping.")
                        break
                except Exception as exc:
                    logger.error("Error on page %d: %s", page, exc)
                    break

        logger.info("Total quotes collected: %d", len(all_items))
        return all_items
