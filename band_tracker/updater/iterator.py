import logging
from typing import AsyncIterator

import httpx
from httpx import URL

from band_tracker.updater.errors import (
    InvalidResponseStructureError,
    InvalidTokenError,
    RateLimitQuotaViolation,
    UnexpectedFaultResponseError,
)

log = logging.getLogger(__name__)


class CustomRequest(httpx.AsyncClient):
    def __init__(self, url: URL, query_params: dict[str, str]) -> None:
        super().__init__()
        self.url = url
        self.query_params = query_params

    async def make_request(self, page_number: int = 0) -> dict[str, dict]:
        response = httpx.get(
            self.url, params={**self.query_params, "page": page_number}
        )
        return response.json()


class PageIterator(AsyncIterator):
    def __init__(self, client: CustomRequest) -> None:
        self.client = client
        self.page_number = 0
        self.buffer: list[dict[str, dict]] = []
        self.stop_flag = False
        self.rate_count = 0

    async def __anext__(self) -> dict[str, dict] | Exception:
        if not self.stop_flag:
            if not self.buffer:
                self.buffer.append(await self.client.make_request(self.page_number))
                self.page_number += 1

            data = self.buffer.pop(0)
            try:
                page_info = data.get("page", {})
                pages_number = page_info.get("totalPages")

                if pages_number is None:
                    return InvalidResponseStructureError(
                        "Pages information not found in response"
                    )
            except AttributeError:
                try:
                    error_response = data.get("fault", {})
                    detail = error_response.get("detail", {})
                    error_message = detail.get("errorcode")
                    match error_message:
                        case None:
                            return InvalidResponseStructureError(
                                "Unexpected Error, fault tstring not found in response"
                            )
                        case "oauth.v2.InvalidApiKey":
                            return InvalidTokenError()
                        case "policies.ratelimit.QuotaViolation":
                            if self.rate_count > 0:
                                return RateLimitQuotaViolation()
                            else:
                                self.rate_count += 1
                                self.page_number -= 1
                        case _:
                            return UnexpectedFaultResponseError("Bruh")
                except AttributeError:
                    return InvalidResponseStructureError(
                        f"Invalid JSON structure: {data}"
                    )
                return InvalidResponseStructureError(f"Invalid JSON structure: {data}")

            if self.page_number == pages_number:
                self.stop_flag = True

            if self.page_number > pages_number:
                raise StopAsyncIteration

            self.rate_count = 0
            return data
        else:
            raise StopAsyncIteration
