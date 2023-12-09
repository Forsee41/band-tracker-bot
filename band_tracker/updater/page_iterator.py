import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from iso3166 import countries

from band_tracker.updater.ApiClient import (
    ApiClientArtists,
    ApiClientEvents,
    exception_helper,
)
from band_tracker.updater.errors import PredictorError, WrongChunkException
from band_tracker.updater.timestamp_predictor import TimestampPredictor

log = logging.getLogger(__name__)
lock = asyncio.Lock()


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
    entities_number: int
    pages: dict[int, PageProgression] = field(default_factory=dict)
    progression: ChunkProgression = ChunkProgression.has_idle
    country_code: str = field(default="")

    def __post_init__(self) -> None:
        self.pages = {
            page_num: PageProgression.idle for page_num in range(self.pages_number)
        }


class ArtistProgression(Enum):
    in_progress = "in_progress"
    done = "done"
    idle = "idle"


@dataclass
class ArtistRequestEntity:
    id_: int
    keyword: str
    progression: ArtistProgression = ArtistProgression.idle


class PageIterator(ABC):
    @abstractmethod
    def __aiter__(self) -> "PageIterator":
        pass

    @abstractmethod
    async def __anext__(self) -> dict[str, dict]:
        pass


class EventIterator(PageIterator):
    def __init__(self, client: ApiClientEvents, predictor: TimestampPredictor) -> None:
        self.client = client
        self.predictor = predictor
        self.chunks: list[EventsChunk] = []
        self.max_end_time = datetime.now()
        self.iterator_start = datetime.now()

    async def _process_large_chunk(self, chunk: EventsChunk) -> EventsChunk:
        for country in countries:
            country_code = country.alpha2
            response = await self.client.make_request(
                chunk.start_datetime,
                chunk.end_datetime,
                country_code=country_code,
            )
            pagination_info = exception_helper(response)

            result_entities = pagination_info.get("elements_number", 0)
            pages_number = pagination_info.get("pages_number", 0)

            if result_entities == 0:
                continue

            chunk = EventsChunk(
                start_datetime=chunk.start_datetime,
                end_datetime=chunk.end_datetime,
                pages_number=pages_number,
                country_code=country_code,
                entities_number=result_entities,
            )
            self.chunks.append(chunk)

        return chunk

    async def _get_chunk(self) -> EventsChunk | None:
        """
        Get the next available undone chunk from the
        list of known chunks; Creates a chunk if no idle.
        -------
        """

        for chunk in self.chunks:
            if (
                chunk.progression != ChunkProgression.done
                and chunk.progression != ChunkProgression.no_idle
            ):
                if PageProgression.idle in chunk.pages.values():
                    return chunk
                elif PageProgression.in_progress in chunk.pages.values():
                    chunk.progression = ChunkProgression.no_idle
                else:
                    chunk.progression = ChunkProgression.done

        async with lock:
            new_chunk = await self._create_chunk()

        if not new_chunk:
            return None

        if new_chunk.end_datetime > self.max_end_time:
            self.max_end_time = new_chunk.end_datetime

        if new_chunk.start_datetime == new_chunk.end_datetime == self.max_end_time:
            self.max_end_time += timedelta(days=1)

        if new_chunk.entities_number >= 1000:
            processed_chunk = await self._process_large_chunk(new_chunk)
            return processed_chunk
        else:
            self.chunks.append(new_chunk)
            return new_chunk

    async def _create_chunk(self) -> EventsChunk | None:
        """
        Creates and returns a chunk;
        returns None instead if only a chunk with 0 elements can be
        created or if the date is more than 2 years away
        -------
        """
        log.debug(
            "++++++++++++++++++++++++++++++++++++   "
            "create_chunk invoke   ++++++++++++++++++++++++++++++++++++"
        )
        eventsChunk = None
        start_time = self.max_end_time
        max_entities = target_entities = result_entities = 1000
        while result_entities >= max_entities:
            try:
                end_time = await self.predictor.get_next_timestamp(
                    start=start_time, target_entities=target_entities
                )
            except Exception as e:
                raise PredictorError(
                    f"Predictor stopped working "
                    f"due to the following error: {str(e)}"
                )

            if start_time > end_time:
                end_time = start_time

            response = await self.client.make_request(start_time, end_time)

            pagination_info = exception_helper(response)

            result_entities = pagination_info.get("elements_number", 0)
            pages_number = pagination_info.get("pages_number", 0)

            eventsChunk = EventsChunk(
                start_datetime=start_time,
                end_datetime=end_time,
                pages_number=pages_number,
                entities_number=result_entities,
            )
            log.debug(str(result_entities) + " " + str(target_entities))

            if result_entities > 1000 and end_time == start_time:
                break

            if result_entities > 2000:
                target_entities = int(target_entities * 0.5)
            else:
                target_entities = int(target_entities * 0.7)

        if (
            result_entities > 0
            and eventsChunk
            and eventsChunk.end_datetime < self.iterator_start + timedelta(days=731)
        ):
            return eventsChunk
        else:
            return None

    def all_chunks_done(self) -> bool:
        """
        Returns True if  all known chunks are done False otherwise
        -------
        """
        return all(
            [
                True if chunk.progression == ChunkProgression.done else False
                for chunk in self.chunks
            ]
        )

    def __aiter__(self) -> "EventIterator":
        return self

    async def __anext__(self) -> dict[str, dict]:
        log.debug("Chunks:  " + str(self.chunks))
        log.debug("max date:  " + str(self.max_end_time))

        current_chunk = await self._get_chunk()
        if current_chunk:
            pages = current_chunk.pages
            log.debug(pages)
            current_page = next(
                (page for page in pages if pages.get(page) == PageProgression.idle),
                None,
            )
            log.debug(current_page)
            if current_page is not None:
                pages.update({current_page: PageProgression.in_progress})
                data = await self.client.make_request(
                    current_chunk.start_datetime,
                    current_chunk.end_datetime,
                    page_number=current_page,
                    country_code=current_chunk.country_code,
                )
                try:
                    exception_helper(data)
                    pages.update({current_page: PageProgression.done})
                    return data
                except Exception as e:
                    pages.update({current_page: PageProgression.idle})
                    raise e
            else:
                current_chunk.progression = ChunkProgression.no_idle
                raise WrongChunkException
        else:
            raise StopAsyncIteration


class ArtistIterator(PageIterator):
    def __init__(self, client: ApiClientArtists, artists: dict[int, str]):
        self.client = client
        self.artists: list[ArtistRequestEntity] = [
            ArtistRequestEntity(id_, name) for id_, name in artists.items()
        ]

    def __aiter__(self) -> "ArtistIterator":
        return self

    async def _get_next_keyword(self) -> ArtistRequestEntity | None:
        for artist in self.artists:
            if (
                artist.progression != ArtistProgression.done
                and artist.progression != ArtistProgression.in_progress
            ):
                return artist
        return None

    async def __anext__(self) -> dict[str, dict]:
        current_keyword = await self._get_next_keyword()
        if current_keyword:
            current_keyword.progression = ArtistProgression.in_progress
            data = await self.client.make_request(keyword=current_keyword.keyword)

            exception_helper(data)
            current_keyword.progression = ArtistProgression.done
            return data

        else:
            raise StopAsyncIteration
