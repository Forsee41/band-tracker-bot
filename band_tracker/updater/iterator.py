import logging
from typing import AsyncIterator

import httpx
from httpx import URL

from band_tracker.core.enums import EventSource
from band_tracker.core.errors import DeserializationError

log = logging.getLogger(__name__)


class CustomRequest(httpx.AsyncClient):
    def __init__(self, url: URL, query_params: dict[str, str]):
        super().__init__()
        self.url = url
        self.query_params = query_params

    async def make_request(self, page_number: int = 0) -> dict[str, dict]:
        response = httpx.get(
            self.url, params={**self.query_params, "page": page_number}
        )
        return response.json()

    async def pages_number(self) -> int:
        data = await self.make_request()
        try:
            log.debug("PENIS")
            page_info = data.get("page", {})
            return page_info.get("totalPages")
        except AttributeError:
            raise DeserializationError("invalid json", EventSource.ticketmaster_api)


class Iterator(AsyncIterator):
    def __init__(self, client: CustomRequest) -> None:
        self.client = client
        self.page_number = 0
        self.buffer: list = []

    async def __anext__(self) -> dict[str, dict]:
        if self.page_number <= await self.client.pages_number() - 1:
            if not self.buffer:
                self.buffer += await self.client.make_request(self.page_number)
                self.page_number += 1

            data = self.buffer.pop(0)
            return data
        else:
            raise StopAsyncIteration
