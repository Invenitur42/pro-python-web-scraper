# Pro Python Web Scraper

A clean, modular, production-oriented web scraping toolkit written in pure Python.
Designed for intermediate-to-advanced scrapers who want something better than a pile of one-off scripts.

**Now includes a simple web UI** — paste a URL, define the fields you want via CSS selectors, and download CSV / JSON / Parquet.

## Features

- **Async-first** with `httpx` + `asyncio` for high concurrency
- **Robust request layer**: retries with exponential backoff, timeouts, user-agent rotation
- **Rate limiting** (token bucket) to be polite and avoid bans
- **Data validation** with Pydantic models
- **Multiple export formats**: JSON, CSV, Parquet
- **Web UI + API**: define fields on the fly and download results
- **Config-driven** via YAML + environment variables
- **Structured logging** (JSON or pretty)
- **CLI** powered by Typer
- **Example spiders** for common patterns
- **Extensible architecture** — easy to add new spiders, middlewares, pipelines

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
```

### Option A — Web UI (easiest)

```bash
scraper-web
# or: python -m scraper.web.app
```

Then open **http://localhost:8000**

1. Paste a URL
2. (Optional) set a repeating-item CSS selector (e.g. `div.quote`)
3. Add the fields you want: column name + CSS selector (+ optional attribute)
4. Choose format (CSV / JSON / Parquet)
5. Click **Scrape & Download**

### Option B — CLI

```bash
scraper run quotes --pages 5 --format json
```

### Option C — Programmatic

```python
import asyncio
from scraper.spiders.quotes import QuotesSpider
from scraper.pipelines.export import JSONExporter

async def main():
    spider = QuotesSpider(max_pages=5)
    items = await spider.run()
    exporter = JSONExporter("data/quotes.json")
    await exporter.export(items)

asyncio.run(main())
```

## How the Web UI works

You tell the scraper **exactly** which pieces of data you want by providing CSS selectors.

Example for https://quotes.toscrape.com:

| Column name | CSS selector       | Attribute |
|-------------|--------------------|-----------|
| text        | `span.text`        | (empty)   |
| author      | `small.author`     | (empty)   |
| tags        | `div.tags a.tag`   | (empty)   |

Optional “Repeating item selector”: `div.quote`  
→ the scraper finds every matching block and extracts the fields inside each one.

This keeps extraction explicit and reliable — no guessing, no AI magic.

## Project Structure

```
pro-python-web-scraper/
├── src/scraper/
│   ├── core/           # HTTP client, rate limiter, exceptions
│   ├── models/         # Pydantic models
│   ├── spiders/        # Individual scrapers
│   ├── pipelines/      # Export helpers
│   ├── web/            # FastAPI UI + API
│   │   ├── app.py
│   │   └── templates/
│   ├── utils/
│   └── cli.py
├── config/
├── tests/
├── examples/
└── pyproject.toml
```

## Design Philosophy

This is intentionally **not** Scrapy. Key principles:

1. **Explicit over magic** — you see every request, selector, and transform.
2. **Composable** — spiders, clients, and pipelines are independent.
3. **Observable** — structured logs.
4. **Safe by default** — rate limits, timeouts, respectful User-Agents.

## Requirements

- Python 3.10+

## License

MIT
