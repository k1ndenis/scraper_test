from __future__ import annotations

import asyncio
from typing import Self

import httpx


class ScraperHttpClient:
    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
        *,
        max_concurrency: int = 10,
        max_attempts: int = 3,
        backoff_base: float = 0.5,
    ) -> None:
        if max_concurrency < 1:
            raise ValueError("max_concurrency must be at least 1")
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")

        self._client = client or httpx.AsyncClient()
        self._owns_client = client is None
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._max_attempts = max_attempts
        self._backoff_base = backoff_base

    async def get_text(self, url: str) -> str:
        last_error: httpx.HTTPError | None = None

        for attempt in range(self._max_attempts):
            try:
                async with self._semaphore:
                    response = await self._client.get(url)
                response.raise_for_status()
                return response.text
            except httpx.HTTPStatusError as error:
                if error.response.status_code < 500:
                    raise
                last_error = error
            except httpx.RequestError as error:
                last_error = error

            if attempt < self._max_attempts - 1:
                await asyncio.sleep(self._backoff_base * (2**attempt))

        assert last_error is not None
        raise last_error

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()
