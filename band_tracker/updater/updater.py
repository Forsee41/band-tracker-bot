import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Coroutine

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

log = logging.getLogger(__name__)


class ClientFactory:
    def __init__(self, base_url: str, token: str) -> None:
        self.base_url = base_url
        self.token = token
        self.params: dict = {"apikey": self.token, "segmentId": "KZFzniwnSyZfZ7v7nJ"}

    def get_events_client(self) -> ApiClient:
        url = self.base_url.join("events")
        return ApiClient(url=url, query_params=self.params)

    def get_artists_client(self) -> ApiClient:
        url = self.base_url.join("attractions")
        return ApiClient(url=url, query_params=self.params)


class RequiredAction(Enum):
    need_to_sleep = "Need to sleep to wait out ratelimit violation"
    check_exceptions_amount = "Check whether an amount of exceptions exceeds max"
    return_ = "Iterator finished, can safely return"


class Updater:
    def __init__(
        self,
        client_factory: ClientFactory,
        dal: UpdateDAL,
        max_fails: int = 5,
        chunk_size: int = 4,
        ratelimit_violation_sleep_time: int = 5,  # seconds
    ) -> None:
        self.client_factory = client_factory
        self.chunk_size = chunk_size
        self.max_fails = max_fails
        self.dal = dal
        self.ratelimit_violation_sleep_time = ratelimit_violation_sleep_time

    def _get_pages_chunk(self, iterator: PageIterator) -> list[Coroutine] | None:
        coroutines = [
            coro
            for _ in range(self.chunk_size)
            if (coro := anext(iterator, None)) is not None
        ]
        return coroutines if coroutines else None

    async def update_artists(
        self,
    ) -> None:
        client = self.client_factory.get_artists_client()
        page_iterator = PageIterator(client)
        exceptions: list[Exception] = []
        while (chunk := self._get_pages_chunk(page_iterator)) is not None:
            start_time = datetime.now()

            pages = await asyncio.gather(*chunk, return_exceptions=True)
            need_to_sleep = False
            need_to_check_exc_list = False
            for page in pages:
                if isinstance(page, Exception):
                    required_action = await self._process_exceptions(
                        exception=page, target_list=exceptions
                    )
                    match required_action:
                        case RequiredAction.need_to_sleep:
                            need_to_sleep = True
                        case RequiredAction.return_:
                            return
                        case RequiredAction.check_exceptions_amount:
                            need_to_check_exc_list = True

                else:
                    updates = get_all_artists(page)
                    for update in updates:
                        await self.dal.update_artist(update)

            if need_to_check_exc_list and len(exceptions) >= self.max_fails:
                raise UpdateError(
                    "Reached the limit of allowed exceptions", exceptions=exceptions
                )
            if need_to_sleep:
                await asyncio.sleep(self.ratelimit_violation_sleep_time)
            else:
                exec_time: timedelta = datetime.now() - start_time
                time_to_wait = timedelta(seconds=1) - exec_time
                seconds_to_wait = time_to_wait.microseconds / 1_000_000
                if seconds_to_wait > 0:
                    await asyncio.sleep(seconds_to_wait)

    async def _process_exceptions(
        self, exception: Exception, target_list: list[Exception]
    ) -> RequiredAction:
        if isinstance(exception, StopAsyncIteration):
            return RequiredAction.return_
        elif isinstance(exception, InvalidTokenError):
            raise exception
        elif isinstance(exception, QuotaViolation):
            raise exception
        elif isinstance(exception, InvalidResponseStructureError):
            target_list.append(exception)
        elif isinstance(exception, RateLimitViolation):
            return RequiredAction.need_to_sleep
        elif isinstance(exception, Exception):
            target_list.append(exception)
        return RequiredAction.check_exceptions_amount

    async def update_events(self) -> None:
        client = self.client_factory.get_events_client()
        page_iterator = PageIterator(client)
        exceptions: list[Exception] = []
        while (chunk := self._get_pages_chunk(page_iterator)) is not None:
            start_time = datetime.now()

            pages = await asyncio.gather(*chunk, return_exceptions=True)
            need_to_sleep = False
            need_to_check_exc_list = False
            for page in pages:
                if isinstance(page, Exception):
                    required_action = await self._process_exceptions(
                        exception=page, target_list=exceptions
                    )
                    match required_action:
                        case RequiredAction.need_to_sleep:
                            need_to_sleep = True
                        case RequiredAction.return_:
                            return
                        case RequiredAction.check_exceptions_amount:
                            need_to_check_exc_list = True

                else:
                    updates = get_all_events(page)
                    for update in updates:
                        await self.dal.update_event(update)

            if need_to_check_exc_list and len(exceptions) >= self.max_fails:
                raise UpdateError(
                    "Reached the limit of allowed exceptions", exceptions=exceptions
                )
            if need_to_sleep:
                await asyncio.sleep(self.ratelimit_violation_sleep_time)
            else:
                exec_time: timedelta = datetime.now() - start_time
                time_to_wait = timedelta(seconds=1) - exec_time
                seconds_to_wait = time_to_wait.microseconds / 1_000_000
                if seconds_to_wait > 0:
                    await asyncio.sleep(seconds_to_wait)
