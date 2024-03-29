import asyncio
import json
import os
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any, AsyncGenerator, Coroutine, Generator, Never

import pytest
import pytest_asyncio
from dotenv import load_dotenv
from sqlalchemy import Engine, create_engine, select, text
from sqlalchemy.orm import joinedload

from band_tracker.core.enums import EventSource
from band_tracker.core.user import RawUser
from band_tracker.core.user_settings import UserSettings
from band_tracker.db.artist_update import ArtistUpdate
from band_tracker.db.dal_bot import BotDAL
from band_tracker.db.dal_message import MessageDAL
from band_tracker.db.dal_update import UpdateDAL
from band_tracker.db.event_update import EventUpdate
from band_tracker.db.models import (
    ArtistDB,
    ArtistTMDataDB,
    Base,
    EventDB,
    EventTMDataDB,
    GenreDB,
)
from band_tracker.db.session import AsyncSessionmaker
from band_tracker.updater.timestamp_predictor import LinearPredictor, TimestampPredictor


@pytest_asyncio.fixture(autouse=True)
async def clean_tables(sync_engine: Engine) -> AsyncGenerator:
    yield
    table_names = [
        "artist",
        "artist_genre",
        "artist_tm_data",
        "event",
        "event_artist",
        "event_tm_data",
        "follow",
        "genre",
        "sales",
        '"user"',
        "user_settings",
        "artist_socials",
        "artist_alias",
        "message",
    ]
    tables_str = ", ".join(table_names)
    command = f"TRUNCATE TABLE {tables_str};"
    with sync_engine.connect() as connection:
        connection.execute(text(command))
        connection.commit()


@pytest.fixture(scope="session")
def event_loop(request: Never) -> Generator:
    assert request
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def sync_engine(db_creds: dict) -> Engine:
    login = db_creds["login"]
    pw = db_creds["password"]
    ip = db_creds["ip"]
    port = db_creds["port"]
    db = db_creds["database"]
    db_url = f"postgresql://" f"{login}:" f"{pw}@" f"{ip}:" f"{port}/" f"{db}"

    engine = create_engine(db_url)
    return engine


@pytest.fixture(scope="session")
def load_dotenv_() -> None:
    load_dotenv()


@pytest.fixture(scope="session")
def db_creds(load_dotenv_: None) -> dict:
    assert load_dotenv_ is None
    db_creds = {
        "login": os.getenv("TEST_DB_LOGIN"),
        "password": os.getenv("TEST_DB_PASSWORD"),
        "ip": os.getenv("TEST_DB_IP"),
        "port": os.getenv("TEST_DB_PORT"),
        "database": os.getenv("TEST_DB_NAME"),
    }
    return db_creds


@pytest.fixture(scope="session", autouse=True)
def create_tables(sync_engine: Engine) -> None:
    Base.metadata.create_all(sync_engine)


@pytest.fixture(scope="session", autouse=True)
def make_text_search_db_preparations(sync_engine: Engine) -> None:
    add_extension_stmt = text("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    create_text_index_stmt = text(
        "CREATE INDEX IF NOT EXISTS artist_alias_gin_trgm_idx ON "
        "artist_alias USING gin (alias gin_trgm_ops)"
    )
    with sync_engine.connect() as connection:
        connection.execute(add_extension_stmt)
        connection.execute(create_text_index_stmt)
        connection.commit()


@pytest.fixture(scope="session")
def get_artist_update() -> Callable[[str], ArtistUpdate]:
    def generate_update(name: str = "gosha") -> ArtistUpdate:
        artists_file_dir = "tests/test_data/artists"
        with open(f"{artists_file_dir}/{name}.json", "r") as f:
            artist_dict = json.load(f)
        update = ArtistUpdate(**artist_dict)
        return update

    return generate_update


@pytest.fixture(scope="session")
def get_event_update() -> Callable[[str], EventUpdate]:
    def generate_update(name: str = "eurovision") -> EventUpdate:
        events_file_dir = "tests/test_data/events"
        with open(f"{events_file_dir}/{name}.json", "r") as f:
            event_dict = json.load(f)
        update = EventUpdate(**event_dict)

        event_name_to_ids = {
            "concert": ["anton_tm_id"],
            "fest": ["anton_tm_id", "clara_tm_id"],
            "eurovision": ["anton_tm_id", "clara_tm_id", "gosha_tm_id"],
        }
        artist_ids = event_name_to_ids.get(
            name, ["anton_tm_id", "clara_tm_id", "gosha_tm_id"]
        )
        artists = [
            ArtistUpdate(
                name="",
                source_specific_data={EventSource.ticketmaster_api: {"id": artist_id}},
                tickets_link=None,
                main_image=None,
                thumbnail_image=None,
                description=None,
            )
            for artist_id in artist_ids
        ]
        update.artists.extend(artists)

        return update

    return generate_update


@pytest.fixture(scope="session")
def get_linear_predictor() -> Callable[[float, float], LinearPredictor]:
    def get_predictor(a: float, b: float) -> LinearPredictor:
        start_time = datetime(year=2000, month=1, day=1)
        predictor = LinearPredictor(a=a, b=b, start=start_time)
        return predictor

    return get_predictor


@pytest.fixture(scope="session")
def get_timestamp_predictor() -> Callable[[timedelta], TimestampPredictor]:
    class MockPredictor(TimestampPredictor):
        def __init__(self, delta: timedelta, start: datetime = datetime.now()) -> None:
            self.delta = delta
            self._start = start

        async def get_next_timestamp(
            self, start: datetime, target_entities: int
        ) -> datetime:
            assert target_entities or not target_entities
            return start + self.delta

        async def update_params(self) -> None:
            pass

        def start(self) -> datetime:
            return self._start

    def get_predictor(delta: timedelta) -> TimestampPredictor:
        predictor = MockPredictor(delta)
        return predictor

    return get_predictor


@pytest.fixture()
def query_artist(
    sessionmaker: AsyncSessionmaker,
) -> Callable[[str], Coroutine[Any, Any, ArtistDB | None]]:
    async def get_artist(tm_id: str) -> ArtistDB | None:
        stmt = (
            select(ArtistDB)
            .join(ArtistTMDataDB)
            .where(ArtistTMDataDB.id == tm_id)
            .options(
                joinedload(ArtistDB.aliases),
                joinedload(ArtistDB.follows),
                joinedload(ArtistDB.genres),
                joinedload(ArtistDB.socials),
                joinedload(ArtistDB.events),
                joinedload(ArtistDB.tm_data),
                joinedload(ArtistDB.event_artist),
            )
        )
        async with sessionmaker.session() as session:
            scalars = await session.scalars(stmt)
            artist_db = scalars.first()
            return artist_db

    return get_artist


@pytest.fixture()
def query_genre(
    sessionmaker: AsyncSessionmaker,
) -> Callable[[str], Coroutine[Any, Any, GenreDB | None]]:
    async def get_genre(genre_id: str) -> GenreDB | None:
        stmt = select(GenreDB).where(GenreDB.id == genre_id)
        async with sessionmaker.session() as session:
            scalars = await session.scalars(stmt)
            genre_db = scalars.first()
            return genre_db

    return get_genre


@pytest.fixture()
def query_event(
    sessionmaker: AsyncSessionmaker,
) -> Callable[[str], Coroutine[Any, Any, EventDB | None]]:
    async def get_event(tm_id: str) -> EventDB | None:
        stmt = (
            select(EventDB)
            .join(EventTMDataDB)
            .where(EventTMDataDB.id == tm_id)
            .options(
                joinedload(EventDB.tm_data),
                joinedload(EventDB.artists),
                joinedload(EventDB.sales),
            )
        )
        async with sessionmaker.session() as session:
            scalars = await session.scalars(stmt)
            event_db = scalars.first()
            return event_db

    return get_event


@pytest.fixture(scope="session")
def sessionmaker(db_creds: dict) -> AsyncSessionmaker:
    sessionmaker = AsyncSessionmaker(**db_creds)
    return sessionmaker


@pytest.fixture(scope="class")
def update_dal(sessionmaker: AsyncSessionmaker) -> UpdateDAL:
    dal = UpdateDAL(sessionmaker)
    return dal


@pytest.fixture(scope="class")
def message_dal(sessionmaker: AsyncSessionmaker) -> MessageDAL:
    dal = MessageDAL(sessionmaker)
    return dal


@pytest.fixture(scope="class")
def bot_dal(sessionmaker: AsyncSessionmaker) -> BotDAL:
    dal = BotDAL(sessionmaker)
    return dal


@pytest.fixture(scope="session")
def user() -> Callable[[int, str], RawUser]:
    def get_user(id: int, name: str) -> RawUser:
        join_date = datetime(year=2000, month=1, day=1)
        user_settings = UserSettings.default()
        user = RawUser(
            tg_id=id,
            name=name,
            join_date=join_date,
            settings=user_settings,
            follows={},
        )
        id += 1
        return user

    return get_user


@pytest.fixture()
def mock_response() -> Callable[[str], dict]:
    def get_response(name: str = "invalid_structure_error") -> dict:
        file_path = "tests/test_data/iterator_mock"
        with open(f"{file_path}/{name}.json", "r") as f:
            response_dict = json.load(f)

        return response_dict

    return get_response
