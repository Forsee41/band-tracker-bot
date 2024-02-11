import asyncio
import logging
from datetime import datetime, timedelta
from typing import Awaitable, Callable, Coroutine
from uuid import UUID

from band_tracker.db.dal_update import UpdateDAL
from band_tracker.db.event_update import EventUpdate
from band_tracker.mq.messages import EventUpdateFinished
from band_tracker.mq.publisher import MQPublisher
from band_tracker.updater.api_client import ApiClientArtists, ApiClientEvents
from band_tracker.updater.deserializator import get_all_artists, get_all_events
from band_tracker.updater.errors import (
    AllTokensViolation,
    EmptyResponseException,
    InvalidResponseStructureError,
    InvalidTokenError,
    PredictorError,
    QuotaViolation,
    RateLimitViolation,
    UpdateError,
    WrongChunkException,
)
from band_tracker.updater.page_iterator import (
    ArtistIterator,
    EventIterator,
    PageIterator,
)
from band_tracker.updater.timestamp_predictor import TimestampPredictor

log = logging.getLogger(__name__)
lock = asyncio.Lock()


class ClientFactory:
    def __init__(self, base_url: str, tokens: list[str]) -> None:
        self.base_url = base_url
        self.tokens = tokens
        self.params: dict = {
            "apikey": self.tokens[0],
            "segmentId": "KZFzniwnSyZfZ7v7nJ",
            "size": 200,
        }

    def get_events_client(self) -> ApiClientEvents:
        url = "".join((self.base_url, "events"))
        return ApiClientEvents(url=url, query_params=self.params, tokens=self.tokens)

    def get_artists_client(self) -> ApiClientArtists:
        url = "".join((self.base_url, "attractions"))
        return ApiClientArtists(url=url, query_params=self.params, tokens=self.tokens)


class Updater:
    def __init__(
        self,
        client_factory: ClientFactory,
        dal: UpdateDAL,
        mq_publisher: MQPublisher,
        predictor: TimestampPredictor | None = None,
        max_fails: int = 5,
        chunk_size: int = 4,
        ratelimit_violation_sleep_time: int = 5,  # seconds
    ) -> None:
        self.client_factory = client_factory
        self.chunk_size = chunk_size
        self.max_fails = max_fails
        self.predictor = predictor
        self.dal = dal
        self.ratelimit_violation_sleep_time = ratelimit_violation_sleep_time
        self.publisher = mq_publisher

    def _get_pages_chunk(self, iterator: PageIterator) -> list[Coroutine] | None:
        coroutines = [
            coro
            for _ in range(self.chunk_size)
            if (coro := anext(iterator, None)) is not None
        ]
        return coroutines if coroutines else None

    async def _process_exceptions(
        self, exception: Exception, target_list: list[Exception]
    ) -> None:
        log.warning(f"Exception registered: {exception}")

        if isinstance(exception, InvalidTokenError):
            raise exception
        elif isinstance(exception, QuotaViolation):
            raise exception
        elif isinstance(exception, AllTokensViolation):
            raise exception
        elif isinstance(exception, PredictorError):
            raise exception
        elif isinstance(exception, InvalidResponseStructureError):
            target_list.append(exception)
        elif isinstance(exception, RateLimitViolation):
            target_list.append(exception)
            await asyncio.sleep(self.ratelimit_violation_sleep_time)
        elif isinstance(exception, EmptyResponseException):
            pass
        elif isinstance(exception, Exception):
            target_list.append(exception)

        if len(target_list) >= self.max_fails:
            raise UpdateError(
                "Reached the limit of allowed exceptions", exceptions=target_list
            )

    async def _update_events_worker(
        self,
        get_elements: Callable[[dict[str, dict]], list],
        client: ApiClientEvents,
        update_dal: Callable[[EventUpdate], Awaitable[tuple[UUID, list[UUID]]]],
    ) -> None:
        if not self.predictor:
            raise PredictorError("Predictor was not given to Updater constructor")

        await self.predictor.update_params()
        page_iterator = EventIterator(client=client, predictor=self.predictor)
        exceptions: list[Exception] = []
        while (chunk := self._get_pages_chunk(page_iterator)) is not None:
            log.debug("coroutines spawn")

            start_time = datetime.now()

            pages = await asyncio.gather(*chunk, return_exceptions=True)

            log.debug(pages)
            if not any(pages):
                return
            for page in pages:
                if page is None or isinstance(page, WrongChunkException):
                    pass
                elif isinstance(page, Exception):
                    await self._process_exceptions(
                        exception=page, target_list=exceptions
                    )

                else:
                    log.info("Successful response. Start parsing")

                    updates = get_elements(page)  # type: ignore
                    for update in updates:
                        event_uuid, _ = await update_dal(update)
                        finished_message = EventUpdateFinished(
                            uuid=event_uuid, created_at=datetime.now()
                        )
                        await self.publisher.send_message(message=finished_message)

            exec_time: timedelta = datetime.now() - start_time
            time_to_wait = timedelta(seconds=1) - exec_time
            seconds_to_wait = time_to_wait.microseconds / 1_000_000
            if seconds_to_wait > 0:
                await asyncio.sleep(seconds_to_wait)

    async def _update_artists_worker(
        self,
        get_elements: Callable[[dict[str, dict]], list],
        client: ApiClientArtists,
        update_dal: Callable,
        artists: list[str],
    ) -> None:
        page_iterator = ArtistIterator(client, artists)
        exceptions: list[Exception] = []

        while (chunk := self._get_pages_chunk(page_iterator)) is not None:
            log.debug("coroutines spawn")

            pages = await asyncio.gather(*chunk, return_exceptions=True)

            if not any(pages):
                return
            for page in pages:
                if isinstance(page, QuotaViolation):
                    client.change_token_flag = True
                elif isinstance(page, Exception):
                    await self._process_exceptions(
                        exception=page, target_list=exceptions
                    )

                else:
                    log.info("Successful response. Start parsing")
                    try:
                        updates = get_elements(page)  # type: ignore
                        for update in updates:
                            # log.debug("UPDATE " + str(update))
                            await update.set_description()
                            await update_dal(update)
                    except EmptyResponseException:
                        pass

    async def update_events(self) -> None:
        log.info("Update Events")

        update_dal = self.dal.update_event
        client = self.client_factory.get_events_client()

        await self._update_events_worker(get_all_events, client, update_dal)

    async def update_artists(self, artists: list[str]) -> None:
        log.info("Update Artists")

        update_dal = self.dal.update_artist
        client = self.client_factory.get_artists_client()

        await self._update_artists_worker(get_all_artists, client, update_dal, artists)
