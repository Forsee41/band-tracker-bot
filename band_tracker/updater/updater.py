import asyncio
from datetime import datetime, timedelta
from typing import Callable, Coroutine, Protocol


class APIClient:
    def __init__(self, token: str, url: str, query_params: dict[str, dict]) -> None:
        """client"""
        self.token = token
        self.url = url
        self.params = query_params

    async def make_request(self, page_number: int) -> dict[str, dict]:
        """request"""
        assert page_number
        return {}


class PageIterator:
    def __init__(self, client: APIClient) -> None:
        assert client
        """hello"""

    async def __anext__(self) -> dict[str, dict]:
        """hello"""
        return {}


class ClientFactory:
    def __init__(self, url: str, token: str) -> None:
        self.url = url
        self.token = token

    def get_events_client(self) -> APIClient:
        params = {}
        return APIClient(token=self.token, url=self.url, query_params=params)

    def get_artists_client(self) -> APIClient:
        params = {}
        return APIClient(token=self.token, url=self.url, query_params=params)


class DbClient(Protocol):
    def do_something_events(self, page: list[dict]) -> None:
        ...

    def do_something_artists(self, page: list[dict]) -> None:
        ...


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
        db_client: DbClient,
    ) -> None:
        self.client_factory = client_factory
        self.chunk_size = chunk_size
        self.max_fails = max_fails
        self.db_client = db_client

    def _get_pages_chunk(self, iterator: PageIterator) -> list[Coroutine] | None:
        coroutines = [
            coro
            for _ in range(self.chunk_size)
            if (coro := anext(iterator, None)) is not None
        ]
        return coroutines if coroutines else None

    async def _update(
        self, client: APIClient, db_handler: Callable[[list[dict]], None]
    ) -> None:
        page_iterator = PageIterator(client)
        exceptions: list[Exception] = []
        while (chunk := self._get_pages_chunk(page_iterator)) is not None:
            start_time = datetime.now()

            pages = await asyncio.gather(*chunk, return_exceptions=True)
            for page in pages:
                if isinstance(page, Exception):
                    exceptions.append(page)
                else:
                    db_handler(page)
            if len(exceptions) >= self.max_fails:
                raise UpdateException(
                    "Reached the limit of allowed exceptions", exceptions=exceptions
                )
            exec_time: timedelta = datetime.now() - start_time
            time_to_wait = timedelta(seconds=1) - exec_time
            seconds_to_wait = time_to_wait.microseconds / 1_000_000
            if seconds_to_wait > 0:
                await asyncio.sleep(seconds_to_wait)

    async def update_artists(self) -> None:
        client = self.client_factory.get_artists_client()
        db_handler = self.db_client.do_something_artists
        await self._update(client=client, db_handler=db_handler)

    async def update_events(self) -> None:
        client = self.client_factory.get_events_client()
        db_handler = self.db_client.do_something_events
        await self._update(client=client, db_handler=db_handler)
