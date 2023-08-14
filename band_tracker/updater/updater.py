import asyncio
from datetime import datetime, timedelta
from typing import Coroutine

from band_tracker.db.dal import UpdateDAL
from band_tracker.updater.deserializator import get_all_artists, get_all_events
from band_tracker.updater.page_iterator import EventsApiClient, PageIterator


class ClientFactory:
    def __init__(self, url: str, token: str) -> None:
        self.url = url
        self.token = token

    def get_events_client(self) -> EventsApiClient:
        params = {}
        return EventsApiClient(url=self.url, query_params=params)

    def get_artists_client(self) -> EventsApiClient:
        params = {}
        return EventsApiClient(url=self.url, query_params=params)


class UpdateException(Exception):
    def __init__(
        self, *args, exceptions: list[Exception], **kwargs  # noqa: ignore
    ) -> None:
        super().__init__(*args, **kwargs)
        self.exceptions = exceptions


class Updater:
    def __init__(
        self,
        client_factory: ClientFactory,
        chunk_size: int,
        max_fails: int,
        dal: UpdateDAL,
    ) -> None:
        self.client_factory = client_factory
        self.chunk_size = chunk_size
        self.max_fails = max_fails
        self.dal = dal

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
            for page in pages:
                if isinstance(page, Exception):
                    exceptions.append(page)
                else:
                    updates = get_all_artists(page)
                    for update in updates:
                        await self.dal.update_artist(update)
            if len(exceptions) >= self.max_fails:
                raise UpdateException(
                    "Reached the limit of allowed exceptions", exceptions=exceptions
                )
            exec_time: timedelta = datetime.now() - start_time
            time_to_wait = timedelta(seconds=1) - exec_time
            seconds_to_wait = time_to_wait.microseconds / 1_000_000
            if seconds_to_wait > 0:
                await asyncio.sleep(seconds_to_wait)

    async def update_events(self) -> None:
        client = self.client_factory.get_events_client()
        page_iterator = PageIterator(client)
        exceptions: list[Exception] = []
        while (chunk := self._get_pages_chunk(page_iterator)) is not None:
            start_time = datetime.now()

            pages = await asyncio.gather(*chunk, return_exceptions=True)
            for page in pages:
                if isinstance(page, Exception):
                    exceptions.append(page)
                else:
                    updates = get_all_events(page)
                    for update in updates:
                        await self.dal.update_event(update)
            if len(exceptions) >= self.max_fails:
                raise UpdateException(
                    "Reached the limit of allowed exceptions", exceptions=exceptions
                )
            exec_time: timedelta = datetime.now() - start_time
            time_to_wait = timedelta(seconds=1) - exec_time
            seconds_to_wait = time_to_wait.microseconds / 1_000_000
            if seconds_to_wait > 0:
                await asyncio.sleep(seconds_to_wait)
