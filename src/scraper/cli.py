"""Command-line interface for the scraper."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from scraper.pipelines.export import get_exporter
from scraper.spiders.quotes import QuotesSpider
from scraper.utils.logging import setup_logging

app = typer.Typer(
    name="scraper",
    help="Production-ready async web scraper",
    add_completion=False,
)
console = Console()


@app.command()
def run(
    spider: str = typer.Argument(..., help="Spider name (currently: quotes)"),
    pages: int = typer.Option(5, "--pages", "-p", help="Max pages to scrape"),
    concurrency: int = typer.Option(5, "--concurrency", "-c", help="Max concurrent requests"),
    delay: float = typer.Option(0.3, "--delay", "-d", help="Delay between requests (seconds)"),
    format: str = typer.Option("json", "--format", "-f", help="Export format: json, csv, parquet"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
    log_level: str = typer.Option("INFO", "--log-level", help="Logging level"),
) -> None:
    """Run a spider and export results."""
    setup_logging(log_level)

    if spider != "quotes":
        console.print(f"[red]Unknown spider: {spider}. Available: quotes[/red]")
        raise typer.Exit(1)

    if output is None:
        output = Path(f"data/{spider}.{format}")

    async def _run() -> None:
        from scraper.core.client import AsyncScraperClient

        client = AsyncScraperClient(concurrency=concurrency, delay=delay)
        spider_instance = QuotesSpider(max_pages=pages, client=client)
        items = await spider_instance.run()

        if not items:
            console.print("[yellow]No items scraped.[/yellow]")
            return

        exporter = get_exporter(format, output)
        await exporter.export(items)
        console.print(f"[green]✓ Scraped {len(items)} items → {output}[/green]")

    asyncio.run(_run())


@app.command()
def version() -> None:
    """Show version."""
    from scraper import __version__

    console.print(f"pro-python-web-scraper v{__version__}")


if __name__ == "__main__":
    app()
