# Pro Python Web Scraper

A clean, modular, production-oriented web scraping toolkit written in pure Python.
Designed for intermediate-to-advanced scrapers who want something better than a pile of one-off scripts.

## Features

- **Async-first** with `httpx` + `asyncio` for high concurrency
- **Robust request layer**: retries with exponential backoff, timeouts, user-agent rotation
- **Rate limiting** (token bucket) to be polite and avoid bans
- **Data validation** with Pydantic models
- **Multiple export formats**: JSON, CSV, Parquet
- **Config-driven** via YAML + environment variables
- **Structured logging** (JSON or pretty)
- **CLI** powered by Typer
- **Example scrapers** for common patterns (quotes, product listings, pagination)
- **Extensible architecture** — easy to add new spiders, middlewares, pipelines

## Project Structure

```
pro-python-web-scraper/
├── src/
│   └── scraper/
│       ├── __init__.py
│       ├── core/
│       │   ├── client.py          # Async HTTP client with retries & rate limiting
│       │   ├── rate_limiter.py
│       │   └── exceptions.py
│       ├── models/                # Pydantic data models
│       ├── spiders/               # Individual scrapers
│       ├── pipelines/             # Export & post-processing
│       ├── utils/
│       └── cli.py
├── config/
│   └── settings.yaml
├── tests/
├── examples/
├── pyproject.toml
├── requirements.txt
├── .env.example
├── .gitignore
└── LICENSE
```

## Quick Start

```bash
# Clone
git clone https://github.com/Invenitur42/pro-python-web-scraper.git
cd pro-python-web-scraper

# Create virtualenv
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install
pip install -e ".[dev]"

# Copy env
cp .env.example .env

# Run example spider
python -m scraper.cli run quotes --pages 3 --output data/quotes.json
```

## Usage Examples

### CLI

```bash
# Scrape quotes (demo site)
scraper run quotes --pages 5 --format json

# Scrape with custom concurrency and delay
scraper run quotes --concurrency 10 --delay 0.5

# Export to parquet
scraper run quotes --format parquet --output data/quotes.parquet
```

### Programmatic

```python
import asyncio
from scraper.spiders.quotes import QuotesSpider
from scraper.pipelines.export import JSONExporter

async def main():
    spider = QuotesSpider(max_pages=5)
    items = await spider.run()
    
    exporter = JSONExporter("data/quotes.json")
    await exporter.export(items)

if __name__ == "__main__":
    asyncio.run(main())
```

## Design Philosophy

This is intentionally **not** Scrapy. Scrapy is excellent for large-scale projects,
but many production needs are better served by a lightweight, explicit, async stack
that you fully control.

Key principles:

1. **Explicit over magic** — you see every request, retry, and transform.
2. **Composable** — spiders, clients, and pipelines are independent.
3. **Observable** — structured logs + metrics hooks.
4. **Safe by default** — rate limits, timeouts, and respectful User-Agents.

## Requirements

- Python 3.10+
- See `pyproject.toml` for full dependency list.

## License

MIT
