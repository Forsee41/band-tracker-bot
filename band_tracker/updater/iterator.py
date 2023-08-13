import asyncio
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


class CustomRequest:
    def __init__(self, url: URL, query_params: dict[str, str]) -> None:
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
        self.rate_limit_error_count = 0

    async def __anext__(self) -> dict[str, dict] | Exception:
        if self.stop_flag:
            raise StopAsyncIteration

        self.buffer.append(await self.client.make_request(self.page_number))
        self.page_number += 1

        data = self.buffer.pop(0)
        try:
            page_info = data.get("page", {})
            pages_number = page_info.get("totalPages")

            if pages_number is None:
                raise InvalidResponseStructureError(
                    f"Pages information not found in response: {page_info}"
                )
        except AttributeError:
            try:
                error_response = data.get("fault", {})
                detail = error_response.get("detail", {})
                error_message = detail.get("errorcode")
                match error_message:
                    case None:
                        raise InvalidResponseStructureError(
                            f"Unexpected Error, "
                            f"fault string not found in response: {error_response}"
                        )
                    case "oauth.v2.InvalidApiKey":
                        raise InvalidTokenError()
                    case "policies.ratelimit.QuotaViolation":
                        await asyncio.sleep(1)
                        if self.rate_limit_error_count > 0:
                            raise RateLimitQuotaViolation(self.page_number)
                        else:
                            self.rate_limit_error_count += 1
                            self.page_number -= 1
                            return await self.__anext__()
                    case _:
                        raise UnexpectedFaultResponseError(
                            f"Unexpected response fault message: {error_message}"
                        )
            except AttributeError:
                raise InvalidResponseStructureError(f"Invalid JSON structure: {data}")

        if self.page_number == pages_number:
            self.stop_flag = True

        if self.page_number > pages_number:
            raise StopAsyncIteration

        self.rate_count = 0
        return data
