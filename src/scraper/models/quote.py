"""Pydantic models for the quotes.toscrape.com demo."""

from __future__ import annotations

from pydantic import BaseModel, Field, HttpUrl


class Quote(BaseModel):
    text: str = Field(..., description="The quote text")
    author: str = Field(..., description="Author name")
    tags: list[str] = Field(default_factory=list)
    author_url: HttpUrl | None = None

    model_config = {"str_strip_whitespace": True}
