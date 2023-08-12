import httpx
from httpx import URL


class CustomRequest(httpx.AsyncClient):
    _base_url = URL("")
    _query_params: dict[str, str] = {}

    async def make_request(self, page_number: int) -> dict[str, dict]:
        response = httpx.get(
            self._base_url, params={**self._query_params, "page": page_number}
        )
        return response.json()


class Iterator:
    def __init__(self, max_pages: int, client: CustomRequest) -> None:
        self.client = client
        self.page_number = 0
        self.max_pages = max_pages
        self.buffer: list = []

    async def __anext__(self) -> dict[str, dict]:
        if not self.buffer:
            self.buffer += await self.client.make_request(self.page_number)
            self.page_number += 1

        data = self.buffer.pop(0)
        return data
