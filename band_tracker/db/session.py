from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


class AsyncSessionmaker:
    def __init__(
        self, login: str, password: str, ip: str, port: str, database: str
    ) -> None:
        self._login = login
        self._password = password
        self._ip = ip
        self._port = port
        self._database = database

        self.engine = self._get_async_engine()
        self.sessionmaker = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    def _get_async_engine(self) -> AsyncEngine:
        db_url = (
            f"postgresql+asyncpg://"
            f"{self._login}:"
            f"{self._password}@"
            f"{self._ip}:"
            f"{self._port}/"
            f"{self._database}"
        )
        return create_async_engine(db_url)

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self.sessionmaker.begin() as session:
            yield session
