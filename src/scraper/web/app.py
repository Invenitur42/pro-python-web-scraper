"""FastAPI web application – paste a URL, define fields, download results."""

from __future__ import annotations

import io
import json
import logging
from typing import Any, Literal

import pandas as pd
from bs4 import BeautifulSoup
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, HttpUrl

from scraper.core.client import AsyncScraperClient
from scraper.utils.logging import setup_logging

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Pro Python Web Scraper",
    description="Paste a URL, define the fields you want via CSS selectors, download the data.",
    version="0.2.0",
)

# Templates live next to this file
from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent / "templates"
STATIC_DIR = Path(__file__).parent / "static"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class FieldDef(BaseModel):
    name: str = Field(..., min_length=1, description="Column name in the output")
    selector: str = Field(..., min_length=1, description="CSS selector")
    attribute: str | None = Field(
        None, description="Optional attribute to extract (e.g. href, src). Leave empty for text."
    )


class ScrapeRequest(BaseModel):
    url: HttpUrl
    fields: list[FieldDef]
    format: Literal["json", "csv", "parquet"] = "csv"
    item_selector: str | None = Field(
        None,
        description="Optional CSS selector for repeating items (e.g. 'div.product'). "
        "If omitted, the whole page is treated as a single item.",
    )


def extract_items(
    html: str,
    fields: list[FieldDef],
    item_selector: str | None = None,
) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "lxml")
    results: list[dict[str, Any]] = []

    containers = soup.select(item_selector) if item_selector else [soup]

    if not containers:
        # Fallback: treat whole page as one item
        containers = [soup]

    for container in containers:
        row: dict[str, Any] = {}
        for field in fields:
            elements = container.select(field.selector)
            if not elements:
                row[field.name] = None
                continue

            values = []
            for el in elements:
                if field.attribute:
                    values.append(el.get(field.attribute))
                else:
                    values.append(el.get_text(strip=True))

            # Single value if only one match, otherwise list
            row[field.name] = values[0] if len(values) == 1 else values

        # Only keep rows that have at least one non-null value
        if any(v is not None and v != "" and v != [] for v in row.values()):
            results.append(row)

    return results


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/scrape")
async def scrape_endpoint(
    url: str = Form(...),
    fields_json: str = Form(..., description="JSON list of {name, selector, attribute?}"),
    format: str = Form("csv"),
    item_selector: str | None = Form(None),
) -> StreamingResponse:
    """Scrape a page according to user-defined fields and return a downloadable file."""
    try:
        fields_data = json.loads(fields_json)
        fields = [FieldDef(**f) for f in fields_data]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid fields JSON: {e}") from e

    if not fields:
        raise HTTPException(status_code=400, detail="At least one field is required")

    format = format.lower()
    if format not in ("json", "csv", "parquet"):
        raise HTTPException(status_code=400, detail="format must be json, csv or parquet")

    try:
        async with AsyncScraperClient(concurrency=3, delay=0.4) as client:
            html = await client.get_text(url)
    except Exception as e:
        logger.exception("Failed to fetch %s", url)
        raise HTTPException(status_code=502, detail=f"Failed to fetch URL: {e}") from e

    items = extract_items(html, fields, item_selector or None)

    if not items:
        raise HTTPException(
            status_code=404,
            detail="No data matched the provided selectors. Check your CSS selectors.",
        )

    # Build file in memory
    if format == "json":
        content = json.dumps(items, indent=2, ensure_ascii=False).encode("utf-8")
        media_type = "application/json"
        filename = "scrape_result.json"
    elif format == "csv":
        df = pd.DataFrame(items)
        buffer = io.StringIO()
        df.to_csv(buffer, index=False)
        content = buffer.getvalue().encode("utf-8")
        media_type = "text/csv"
        filename = "scrape_result.csv"
    else:  # parquet
        df = pd.DataFrame(items)
        buffer = io.BytesIO()
        df.to_parquet(buffer, index=False)
        content = buffer.getvalue()
        media_type = "application/octet-stream"
        filename = "scrape_result.parquet"

    return StreamingResponse(
        io.BytesIO(content),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


def main() -> None:
    import uvicorn

    setup_logging("INFO")
    uvicorn.run(
        "scraper.web.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()
