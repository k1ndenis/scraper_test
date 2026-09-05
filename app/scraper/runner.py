from __future__ import annotations

import asyncio
from dataclasses import dataclass

import httpx

from app.scraper.http_client import ScraperHttpClient
from app.scraper.parser import BookParseError, ParsedBook, parse_book_page


@dataclass(frozen=True, slots=True)
class ProductPageError:
    url: str
    message: str


@dataclass(frozen=True, slots=True)
class ProductPageLoadResult:
    books: list[ParsedBook]
    errors: list[ProductPageError]


async def load_product_pages(
    product_urls: list[str],
    client: ScraperHttpClient,
) -> ProductPageLoadResult:
    
    async def load_one(product_url: str) -> ParsedBook | ProductPageError:
        try:
            html = await client.get_text(product_url)
            return parse_book_page(html, product_url)
        except (BookParseError, httpx.HTTPError) as error:
            return ProductPageError(url=product_url, message=str(error))

    results = await asyncio.gather(
        *(
            load_one(product_url)
            for product_url in product_urls
        )
    )

    books = [result for result in results if isinstance(result, ParsedBook)]

    errors = [result for result in results if isinstance(result, ProductPageError)]

    return ProductPageLoadResult(books=books, errors=errors)
