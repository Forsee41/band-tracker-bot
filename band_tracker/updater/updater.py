import asyncio
import logging
from datetime import datetime, timedelta
from typing import Callable, Coroutine

from band_tracker.db.dal import UpdateDAL
from band_tracker.updater.deserializator import get_all_artists, get_all_events
from band_tracker.updater.errors import (
    InvalidResponseStructureError,
    InvalidTokenError,
    QuotaViolation,
    RateLimitViolation,
    UpdateError,
)
from band_tracker.updater.page_iterator import ApiClient, PageIterator
from band_tracker.updater.timestamp_predictor import TimestampPredictor

log = logging.getLogger(__name__)


class ClientFactory:
    def __init__(self, base_url: str, token: str) -> None:
        self.base_url = base_url
        self.token = token
        self.params: dict = {"apikey": self.token, "segmentId": "KZFzniwnSyZfZ7v7nJ"}

    def get_events_client(self) -> ApiClient:
        url = "".join((self.base_url, "events"))
        return ApiClient(url=url, query_params=self.params)

    def get_artists_client(self) -> ApiClient:
        url = "".join((self.base_url, "attractions"))
        return ApiClient(url=url, query_params=self.params)


class Updater:
    def __init__(
        self,
        client_factory: ClientFactory,
        dal: UpdateDAL,
        predictor: TimestampPredictor,
        max_fails: int = 5,
        chunk_size: int = 4,
        ratelimit_violation_sleep_time: int = 1,  # seconds
    ) -> None:
        self.client_factory = client_factory
        self.chunk_size = chunk_size
        self.max_fails = max_fails
        self.predictor = predictor
        self.dal = dal
        self.ratelimit_violation_sleep_time = ratelimit_violation_sleep_time

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
        elif isinstance(exception, InvalidResponseStructureError):
            target_list.append(exception)
        elif isinstance(exception, RateLimitViolation):
            target_list.append(exception)
            await asyncio.sleep(self.ratelimit_violation_sleep_time)
        elif isinstance(exception, Exception):
            target_list.append(exception)

        if len(target_list) >= self.max_fails:
            raise UpdateError(
                "Reached the limit of allowed exceptions", exceptions=target_list
            )

    async def _update(
        self,
        get: Callable[[dict[str, dict]], list],
        client: ApiClient,
        update_dal: Callable,
    ) -> None:
        page_iterator = PageIterator(client=client, predictor=self.predictor)
        exceptions: list[Exception] = []
        while (chunk := self._get_pages_chunk(page_iterator)) is not None:
            log.debug("coroutines spawn")

            start_time = datetime.now()

            pages = await asyncio.gather(*chunk, return_exceptions=True)
            for page in pages:
                if isinstance(page, StopAsyncIteration):
                    return
                elif isinstance(page, Exception):
                    await self._process_exceptions(
                        exception=page, target_list=exceptions
                    )

                else:
                    log.info("Successful response. Start parsing")

                    updates = get(page)
                    for update in updates:
                        await update_dal(update)

            exec_time: timedelta = datetime.now() - start_time
            time_to_wait = timedelta(seconds=1) - exec_time
            seconds_to_wait = time_to_wait.microseconds / 1_000_000
            if seconds_to_wait > 0:
                await asyncio.sleep(seconds_to_wait)

    async def update_events(self) -> None:
        log.info("Update Events")

        update_dal = self.dal.update_event
        client = self.client_factory.get_events_client()

        await self._update(get_all_events, client, update_dal)

    async def update_artists(self) -> None:
        log.info("Update Artists")

        update_dal = self.dal.update_artist
        client = self.client_factory.get_artists_client()

        await self._update(get_all_artists, client, update_dal)
