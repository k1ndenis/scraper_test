import asyncio
from pathlib import Path

from app.scraper.runner import load_product_pages

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "book_page.html"
PRODUCT_URLS = [
    "https://books.toscrape.com/catalogue/book-one_1/index.html",
    "https://books.toscrape.com/catalogue/book-two_2/index.html",
    "https://books.toscrape.com/catalogue/broken-book_3/index.html",
]


def test_load_product_pages_continues_after_expected_error() -> None:
    class MockScraperHttpClient:
        def __init__(self, pages: dict[str, str]) -> None:
            self.pages = pages
            self.requested_urls: list[str] = []

        async def get_text(self, url: str) -> str:
            self.requested_urls.append(url)
            return self.pages[url]

    book_html = FIXTURE_PATH.read_text()
    client = MockScraperHttpClient(
        {
            PRODUCT_URLS[0]: book_html,
            PRODUCT_URLS[1]: book_html.replace("A Light in the Attic", "Second Book"),
            PRODUCT_URLS[2]: "<html><body></body></html>",
        }
    )

    result = asyncio.run(load_product_pages(PRODUCT_URLS, client))

    assert [book.title for book in result.books] == ["A Light in the Attic", "Second Book"]
    assert result.errors[0].url == PRODUCT_URLS[2]
    assert result.errors[0].message == "Missing required field: title"
    assert set(client.requested_urls) == set(PRODUCT_URLS)
