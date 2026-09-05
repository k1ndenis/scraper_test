from decimal import Decimal
from pathlib import Path

import pytest

from app.scraper.parser import BookParseError, parse_book_page

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "book_page.html"
PAGE_URL = "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"


def test_parse_book_page_extracts_product_data() -> None:
    book = parse_book_page(FIXTURE_PATH.read_text(), PAGE_URL)

    assert book.title == "A Light in the Attic"
    assert book.upc == "a897fe39b1053632"
    assert book.price == Decimal("51.77")
    assert book.stock_quantity == 22
    assert book.rating == 3
    assert book.category == "Poetry"
    assert book.description == "It's hard to imagine a world without A Light in the Attic."
    assert book.product_url == PAGE_URL
    assert book.image_url == "https://books.toscrape.com/media/cache/2c/da/2cda5a10.jpg"


def test_parse_book_page_rejects_missing_upc() -> None:
    html = "<html><body><div class='product_main'><h1>Book</h1></div></body></html>"

    with pytest.raises(BookParseError, match="Missing required field: UPC"):
        parse_book_page(html, PAGE_URL)
