import asyncio

import httpx
import pytest

from app.scraper.http_client import ScraperHttpClient


def test_get_text_retries_after_server_error() -> None:
    requests_count = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal requests_count
        requests_count += 1
        if requests_count == 1:
            return httpx.Response(500, request=request)
        return httpx.Response(200, text="<html>ok</html>", request=request)

    async def scenario() -> str:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            scraper_client = ScraperHttpClient(client, backoff_base=0)
            return await scraper_client.get_text("https://example.test/book")

    assert asyncio.run(scenario()) == "<html>ok</html>"
    assert requests_count == 2


def test_get_text_does_not_retry_client_error() -> None:
    requests_count = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal requests_count
        requests_count += 1
        return httpx.Response(404, request=request)

    async def scenario() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            scraper_client = ScraperHttpClient(client, backoff_base=0)
            await scraper_client.get_text("https://example.test/book")

    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(scenario())

    assert requests_count == 1


def test_get_text_retries_after_request_error() -> None:
    requests_count = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal requests_count
        requests_count += 1
        if requests_count == 1:
            raise httpx.ConnectError("Connection failed", request=request)
        return httpx.Response(200, text="<html>ok</html>", request=request)

    async def scenario() -> str:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            scraper_client = ScraperHttpClient(client, backoff_base=0)
            return await scraper_client.get_text("https://example.test/book")

    assert asyncio.run(scenario()) == "<html>ok</html>"
    assert requests_count == 2
