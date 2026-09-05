from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.scraper.http_client import ScraperHttpClient


@dataclass(frozen=True, slots=True)
class CatalogPage:
    product_urls: list[str]
    next_page_url: str | None


def parse_catalog_page(html: str, page_url: str) -> CatalogPage:
    """Разбирает одну готовую HTML-страницу каталога."""
    soup = BeautifulSoup(html, "lxml")
    product_urls = [
        urljoin(page_url, link["href"])
        for link in soup.select("article.product_pod h3 a[href]")
    ]
    next_link = soup.select_one("li.next a[href]")

    return CatalogPage(
        product_urls=product_urls,
        next_page_url=urljoin(page_url, next_link["href"]) if next_link else None,
    )


async def collect_product_urls(
    start_url: str,
    client: ScraperHttpClient,
) -> list[str]:
    """Последовательно обходит все страницы каталога и возвращает ссылки на все найденные книги."""
    product_urls: list[str] = []
    seen_product_urls: set[str] = set()
    seen_page_urls: set[str] = set()
    page_url: str | None = start_url

    while page_url and page_url not in seen_page_urls:
        seen_page_urls.add(page_url)
        page = parse_catalog_page(await client.get_text(page_url), page_url)

        for product_url in page.product_urls:
            if product_url not in seen_product_urls:
                seen_product_urls.add(product_url)
                product_urls.append(product_url)

        page_url = page.next_page_url

    return product_urls
