import asyncio
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

    async def make_request(
        self, start_date: datetime, end_date: datetime, page_number: int = 0
    ) -> dict[str, dict]:
        log.debug("+++++++++++++++++++++++++++SEND REQUEST+++++++++++++++++++++++++++")

        reformat_start_date = datetime.strptime(str(start_date), "%Y-%m-%d %H:%M:%S.%f")
        reformat_start_date = reformat_start_date.strftime("%Y-%m-%dT%H:%M:%SZ")

        reformat_end_date = datetime.strptime(str(end_date), "%Y-%m-%d %H:%M:%S.%f")
        reformat_end_date = reformat_end_date.strftime("%Y-%m-%dT%H:%M:%SZ")

        startEndDateTime = f"{reformat_start_date},{reformat_end_date}"
        log.debug(startEndDateTime)
        response = httpx.get(
            self.url,
            params={
                **self.query_params,
                "startEndDateTime": startEndDateTime,
                "page": page_number,
            },
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
    pages_number: int
    start_datetime: datetime
    end_datetime: datetime
    pages: dict[int, PageProgression] = field(default_factory=dict)
    progression: ChunkProgression = ChunkProgression.has_idle

    def __post_init__(self) -> None:
        self.pages = {
            page_num: PageProgression.idle for page_num in range(self.pages_number)
        }


def exception_helper(data: dict[str, dict]) -> dict[str, int]:
    try:
        page_info = data.get("page")
        pages_number = page_info.get("totalPages")  # type: ignore
        elements_number = page_info.get("totalElements")  # type: ignore

        if pages_number is None:
            raise InvalidResponseStructureError(
                f"Pages information not found in response: {page_info}"
            )

        if elements_number is None:
            raise InvalidResponseStructureError(
                f"Total elements information not found in response: {page_info}"
            )

        return {"pages_number": pages_number, "elements_number": elements_number}

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
                    # TODO
                    raise RateLimitViolation
                case _:
                    raise UnexpectedFaultResponseError(
                        f"Unexpected response fault message: {error_message}"
                    )
        except AttributeError:
            raise InvalidResponseStructureError(f"Invalid JSON structure: {data}")


class PageIterator:
    def __init__(self, client: ApiClient, predictor: TimestampPredictor) -> None:
        self.client = client
        self.predictor = predictor
        self.stop_flag = False
        self.chunks: list[EventsChunk] = []
        self.max_end_time = datetime.now()

    async def _get_chunk(self) -> EventsChunk | None:
        """
        Get the next available undone chunk from the list of known chunks; Creates a chunk if all done.
        """
        for chunk in self.chunks:
            if (
                chunk.progression != ChunkProgression.done
                or chunk.progression != ChunkProgression.no_idle
            ):
                if PageProgression.idle in chunk.pages.values():
                    return chunk
                elif PageProgression.in_progress in chunk.pages.values():
                    chunk.progression = ChunkProgression.no_idle
                else:
                    chunk.progression = ChunkProgression.done

        new_chunk = await self._create_chunk()

        if new_chunk.end_datetime > self.max_end_time:
            self.max_end_time = new_chunk.end_datetime

        self.chunks.append(new_chunk)
        return new_chunk

    async def _create_chunk(self) -> EventsChunk | None:
        """
        Creates and returns a chunk; returns None instead if only a chunk with 0 elements can be created.
        """
        eventsChunk = None
        max_entities = target_entities = result_entities = 1000
        while max_entities >= result_entities:
            start_time = self.max_end_time
            end_time = self.predictor.get_next_timestamp(
                start=start_time, target_entities=target_entities
            )
            response = await self.client.make_request(start_time, end_time)
            pagination_info = exception_helper(response)
            result_entities = pagination_info.get("elements_number")
            pages_number = pagination_info.get("pages_number")

            target_entities = int(target_entities * 0.75)

            eventsChunk = EventsChunk(
                start_datetime=start_time,
                end_datetime=end_time,
                pages_number=pages_number,
            )

        if result_entities > 0:
            return eventsChunk
        else:
            return None

    def chunks_done(self) -> bool:
        return all(
            [
                True if chunk.progression == ChunkProgression.done else False
                for chunk in self.chunks
            ]
        )

    def __aiter__(self) -> "PageIterator":
        return self

    async def __anext__(self) -> dict[str, dict]:
        if self.stop_flag:
            raise StopAsyncIteration

        current_chunk = await self._get_chunk()
        if current_chunk:
            pages = current_chunk.pages
            current_page = next(
                (page for page in pages if pages.get(page) == PageProgression.idle),
                None,
            )
            if current_page:
                pages.update({current_page: PageProgression.in_progress})
                data = await self.client.make_request(
                    current_chunk.start_datetime,
                    current_chunk.end_datetime,
                    page_number=current_page,
                )
                exception_helper(data)
                return data
            else:
                # TODO: implement
                raise UnexpectedFaultResponseError
        else:
            if self.chunks_done():
                log.debug("No more elements can be fetched")
                raise StopAsyncIteration
            else:
                await asyncio.sleep(5)
                if not self.chunks_done():
                    log.debug(
                        "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
                    )
                    raise TimeoutError
                else:
                    log.debug("No more elements can be fetched")
                    raise StopAsyncIteration
