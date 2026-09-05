import asyncio
from pathlib import Path

from app.scraper.catalog import collect_product_urls, parse_catalog_page

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "catalog_page.html"
PAGE_ONE_URL = "https://books.toscrape.com/catalogue/page-1.html"
PAGE_TWO_URL = "https://books.toscrape.com/catalogue/page-2.html"


def test_parse_catalog_page_extracts_absolute_urls() -> None:
    page = parse_catalog_page(FIXTURE_PATH.read_text(), PAGE_ONE_URL)

    assert page.product_urls == [
        "https://books.toscrape.com/catalogue/book-one_1/index.html",
        "https://books.toscrape.com/catalogue/book-two_2/index.html",
    ]
    assert page.next_page_url == PAGE_TWO_URL


def test_collect_product_urls_follows_pagination_without_duplicates_or_loops() -> None:
    class MockScraperHttpClient:
        def __init__(self, pages: dict[str, str]) -> None:
            self.pages = pages
            self.requested_urls: list[str] = []

        async def get_text(self, url: str) -> str:
            self.requested_urls.append(url)
            return self.pages[url]

    second_page_html = """
    <article class="product_pod"><h3><a href="book-two_2/index.html">Book two</a></h3></article>
    <article class="product_pod"><h3><a href="book-three_3/index.html">Book three</a></h3></article>
    <li class="next"><a href="page-1.html">next</a></li>
    """
    client = MockScraperHttpClient(
        {
            PAGE_ONE_URL: FIXTURE_PATH.read_text(),
            PAGE_TWO_URL: second_page_html,
        }
    )

    product_urls = asyncio.run(collect_product_urls(PAGE_ONE_URL, client))

    assert product_urls == [
        "https://books.toscrape.com/catalogue/book-one_1/index.html",
        "https://books.toscrape.com/catalogue/book-two_2/index.html",
        "https://books.toscrape.com/catalogue/book-three_3/index.html",
    ]
    assert client.requested_urls == [PAGE_ONE_URL, PAGE_TWO_URL]
