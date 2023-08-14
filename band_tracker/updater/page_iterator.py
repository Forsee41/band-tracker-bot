import logging

import httpx
from httpx import URL

from band_tracker.updater.errors import (
    InvalidResponseStructureError,
    InvalidTokenError,
    RateLimitViolation,
    UnexpectedFaultResponseError,
)

log = logging.getLogger(__name__)


class EventsApiRequest:
    def __init__(self, url: URL, query_params: dict[str, str]) -> None:
        self.url = url
        self.query_params = query_params

    async def make_request(self, page_number: int = 0) -> dict[str, dict]:
        response = httpx.get(
            self.url, params={**self.query_params, "page": page_number}
        )
        return response.json()


class PageIterator:
    def __init__(self, client: EventsApiRequest) -> None:
        self.client = client
        self.page_number = 0
        self.stop_flag = False

    def __aiter__(self) -> "PageIterator":
        return self

    async def __anext__(self) -> dict[str, dict]:
        if self.stop_flag:
            raise StopAsyncIteration

        current_page = self.page_number
        self.page_number += 1
        data = await self.client.make_request(self.page_number)

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
                    case "policies.ratelimit.SpikeArrestViolation":
                        if current_page - 1 < self.page_number:
                            self.page_number = current_page - 1
                        raise RateLimitViolation(self.page_number)
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

        return data
