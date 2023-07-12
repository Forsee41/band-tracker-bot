import asyncio
import json
import os
from collections.abc import Callable
from typing import Generator, Never

import pytest
from dotenv import load_dotenv
from sqlalchemy import Engine, create_engine, text

from band_tracker.core.artist_update import ArtistUpdate
from band_tracker.core.event_update import EventUpdate
from band_tracker.db.dal import DAL
from band_tracker.db.models import Base
from band_tracker.db.session import AsyncSessionmaker


@pytest.fixture(scope="function", autouse=True)
async def clean_tables(sync_engine: Engine) -> None:
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
        "subscription",
        '"user"',
        "user_settings",
        "artist_socials",
    ]
    tables_str = ", ".join(table_names)
    with sync_engine.connect() as connection:
        connection.execute(text(f"TRUNCATE TABLE {tables_str};"))


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


@pytest.fixture(scope="session")
def get_artist_update() -> Callable[[str], ArtistUpdate]:
    def generate_update(name: str) -> ArtistUpdate:
        artists_file_dir = "tests/test_data/artists"
        with open(f"{artists_file_dir}/{name}.json", "r") as f:
            artist_dict = json.load(f)
        update = ArtistUpdate(**artist_dict)
        return update

    return generate_update


@pytest.fixture(scope="session")
def get_event_update() -> Callable[[str], EventUpdate]:
    def generate_update(name: str) -> EventUpdate:
        events_file_dir = "tests/test_data/events"
        with open(f"{events_file_dir}/{name}.json", "r") as f:
            event_dict = json.load(f)
        update = EventUpdate(**event_dict)
        return update

    return generate_update


@pytest.fixture(scope="session")
def sessionmaker(db_creds: dict) -> AsyncSessionmaker:
    sessionmaker = AsyncSessionmaker(**db_creds)
    return sessionmaker


@pytest.fixture(scope="class")
def dal(sessionmaker: AsyncSessionmaker) -> DAL:
    dal = DAL(sessionmaker)
    return dal
