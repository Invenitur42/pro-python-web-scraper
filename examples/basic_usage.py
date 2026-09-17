"""Minimal example of using the scraper programmatically."""

import asyncio
from pathlib import Path

from scraper.core.client import AsyncScraperClient
from scraper.pipelines.export import JSONExporter
from scraper.spiders.quotes import QuotesSpider
from scraper.utils.logging import setup_logging


async def main() -> None:
    setup_logging("INFO")

    client = AsyncScraperClient(concurrency=3, delay=0.4)
    spider = QuotesSpider(max_pages=2, client=client)

    items = await spider.run()
    print(f"Scraped {len(items)} quotes")

    out = Path("data/example_quotes.json")
    exporter = JSONExporter(out)
    await exporter.export(items)
    print(f"Saved to {out}")


if __name__ == "__main__":
    asyncio.run(main())
