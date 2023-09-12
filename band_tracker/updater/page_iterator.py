import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

import httpx

from band_tracker.updater.errors import (
    InvalidResponseStructureError,
    InvalidTokenError,
    RateLimitViolation,
    UnexpectedFaultResponseError,
)
from band_tracker.updater.timestamp_predictor import TimestampPredictor

log = logging.getLogger(__name__)


class ApiClient:
    def __init__(self, url: str, query_params: dict[str, str]) -> None:
        self.url = url
        self.query_params = query_params

    async def make_request(self, page_number: int = 0) -> dict[str, dict]:
        response = httpx.get(
            self.url, params={**self.query_params, "page": page_number}
        )
        return response.json()


class ChunkProgression(Enum):
    no_idle = "no_idle"
    done = "done"
    has_idle = "has_idle"


class PageProgression(Enum):
    in_progress = "in_progress"
    done = "done"
    idle = "idle"


@dataclass
class EventsChunk:
    total_pages: int
    start_datetime: datetime
    end_datetime: datetime
    pages: dict[int, PageProgression] = field(default_factory=dict)
    progression: ChunkProgression = ChunkProgression.has_idle

    def __post_init__(self) -> None:
        self.pages = {
            page_num: PageProgression.idle for page_num in range(self.total_pages)
        }


class PageIterator:
    def __init__(self, client: ApiClient, predictor: TimestampPredictor) -> None:
        self.client = client
        self.predictor = predictor
        self.stop_flag = False
        self.chunks: list[EventsChunk] = []
        self.current_chunk = None

    async def _get_next_chunk(self) -> EventsChunk:
        target_entities = 800
        while True:
            end_timestamp = self.predictor.get_next_timestamp(
                start=self._current_end_time(), target_entities=target_entities
            )
            # TODO: add real entities and pages number check
            real_entities = 500
            pages = 3
            if real_entities < 1000:
                break
            else:
                target_entities = int(target_entities * 0.75)
        return EventsChunk(
            start_datetime=self._current_start_time(),
            end_datetime=end_timestamp,
            total_pages=pages,
        )

    async def initialize(self) -> None:
        self.current_chunk = await self._get_next_chunk()

    def _current_start_time(self) -> datetime:
        if self.current_chunk:
            return self.current_chunk.start_datetime
        else:
            return self.predictor.start

    def _current_end_time(self) -> datetime:
        if self.current_chunk is None:
            return self.predictor.start
        else:
            return self.current_chunk.end_datetime

    def __aiter__(self) -> "PageIterator":
        return self

    async def __anext__(self) -> dict[str, dict]:
        if not self.current_chunk:
            await self.initialize()
        if self.stop_flag:
            raise StopAsyncIteration

        current_page = self.page_number
        self.page_number += 1
        data = await self.client.make_request(self.page_number)

        try:
            page_info = data.get("page")
            pages_number = page_info.get("totalPages")  # type: ignore

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
