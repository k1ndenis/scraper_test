from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Tag


class BookParseError(ValueError):
    ...


@dataclass(frozen=True, slots=True)
class ParsedBook:
    title: str
    upc: str
    price: Decimal
    stock_quantity: int
    rating: int
    category: str
    description: str | None
    product_url: str
    image_url: str


RATING_VALUES = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5,
}


def parse_book_page(html: str, page_url: str) -> ParsedBook:
    """Парсит одну HTML-страницу книги."""
    
    _require_absolute_url(page_url)
    soup = BeautifulSoup(html, "lxml")

    title = _required_text(soup.select_one(".product_main h1"), "title")
    upc = _required_text(_table_value(soup, "UPC"), "UPC")
    price = _parse_price(_required_text(soup.select_one(".price_color"), "price"))
    stock_quantity = _parse_stock_quantity(
        _required_text(soup.select_one(".availability"), "stock quantity")
    )
    rating = _parse_rating(soup.select_one(".star-rating"))
    category = _parse_category(soup)
    description = _parse_description(soup)
    image_url = urljoin(page_url, _required_attribute(soup.select_one("#product_gallery img"), "src", "image"))

    return ParsedBook(
        title=title,
        upc=upc,
        price=price,
        stock_quantity=stock_quantity,
        rating=rating,
        category=category,
        description=description,
        product_url=page_url,
        image_url=image_url,
    )


def _table_value(soup: BeautifulSoup, label: str) -> Tag | None:
    header = soup.find("th", string=label)
    return header.find_next_sibling("td") if header else None


def _required_text(element: Tag | None, field_name: str) -> str:
    if element is None:
        raise BookParseError(f"Missing required field: {field_name}")

    value = element.get_text(" ", strip=True)
    if not value:
        raise BookParseError(f"Missing required field: {field_name}")
    return value


def _required_attribute(element: Tag | None, attribute: str, field_name: str) -> str:
    if element is None or not (value := element.get(attribute)):
        raise BookParseError(f"Missing required field: {field_name}")
    return str(value)


def _parse_price(raw_price: str) -> Decimal:
    try:
        return Decimal(raw_price.replace("£", "").replace(",", ""))
    except InvalidOperation as error:
        raise BookParseError(f"Invalid price: {raw_price}") from error


def _parse_stock_quantity(raw_stock: str) -> int:
    match = re.search(r"\((\d+)\s+available\)", raw_stock, re.IGNORECASE)
    if match is None:
        raise BookParseError(f"Invalid stock quantity: {raw_stock}")
    return int(match.group(1))


def _parse_rating(element: Tag | None) -> int:
    if element is None:
        raise BookParseError("Missing required field: rating")

    for class_name in element.get("class", []):
        if class_name in RATING_VALUES:
            return RATING_VALUES[class_name]
    raise BookParseError("Invalid rating")


def _parse_category(soup: BeautifulSoup) -> str:
    categories = soup.select("ul.breadcrumb li a")
    if len(categories) < 2:
        raise BookParseError("Missing required field: category")
    return _required_text(categories[-1], "category")


def _parse_description(soup: BeautifulSoup) -> str | None:
    heading = soup.select_one("#product_description")
    if heading is None:
        return None

    description = heading.find_next_sibling("p")
    return _required_text(description, "description")


def _require_absolute_url(page_url: str) -> None:
    parsed_url = urlparse(page_url)
    if not parsed_url.scheme or not parsed_url.netloc:
        raise BookParseError(f"Invalid product URL: {page_url}")
