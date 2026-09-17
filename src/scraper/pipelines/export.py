"""Export pipelines for scraped items."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Sequence

import aiofiles
import pandas as pd
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class BaseExporter:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    async def export(self, items: Sequence[BaseModel | dict[str, Any]]) -> None:
        raise NotImplementedError


class JSONExporter(BaseExporter):
    async def export(self, items: Sequence[BaseModel | dict[str, Any]]) -> None:
        data = [
            item.model_dump(mode="json") if isinstance(item, BaseModel) else item
            for item in items
        ]
        async with aiofiles.open(self.path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(data, indent=2, ensure_ascii=False))
        logger.info("Exported %d items → %s", len(data), self.path)


class CSVExporter(BaseExporter):
    async def export(self, items: Sequence[BaseModel | dict[str, Any]]) -> None:
        records = [
            item.model_dump(mode="json") if isinstance(item, BaseModel) else item
            for item in items
        ]
        df = pd.DataFrame(records)
        df.to_csv(self.path, index=False)
        logger.info("Exported %d items → %s", len(records), self.path)


class ParquetExporter(BaseExporter):
    async def export(self, items: Sequence[BaseModel | dict[str, Any]]) -> None:
        records = [
            item.model_dump(mode="json") if isinstance(item, BaseModel) else item
            for item in items
        ]
        df = pd.DataFrame(records)
        df.to_parquet(self.path, index=False)
        logger.info("Exported %d items → %s", len(records), self.path)


def get_exporter(fmt: str, path: str | Path) -> BaseExporter:
    fmt = fmt.lower()
    if fmt == "json":
        return JSONExporter(path)
    if fmt == "csv":
        return CSVExporter(path)
    if fmt == "parquet":
        return ParquetExporter(path)
    raise ValueError(f"Unsupported export format: {fmt}")
