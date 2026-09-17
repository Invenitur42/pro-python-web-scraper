"""Basic tests for the Quotes spider."""

import pytest
from scraper.models.quote import Quote
from scraper.spiders.quotes import QuotesSpider


SAMPLE_HTML = """
<html>
<body>
<div class="quote">
    <span class="text">“The world as we have created it is a process of our thinking.”</span>
    <span>
        by <small class="author">Albert Einstein</small>
        <a href="/author/Albert-Einstein">(about)</a>
    </span>
    <div class="tags">
        <a class="tag" href="/tag/change/page/1/">change</a>
        <a class="tag" href="/tag/deep-thoughts/page/1/">deep-thoughts</a>
    </div>
</div>
</body>
</html>
"""


@pytest.mark.asyncio
async def test_parse_quote() -> None:
    spider = QuotesSpider(max_pages=1)
    items = await spider.parse(SAMPLE_HTML, "https://quotes.toscrape.com")

    assert len(items) == 1
    quote = items[0]
    assert isinstance(quote, Quote)
    assert "process of our thinking" in quote.text
    assert quote.author == "Albert Einstein"
    assert "change" in quote.tags
    assert "deep-thoughts" in quote.tags
