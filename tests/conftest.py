import os

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine

from band_tracker.db.dal import DAL
from band_tracker.db.models import Base
from band_tracker.db.session import AsyncSessionmaker


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
def create_tables(db_creds: dict) -> None:
    login = db_creds["login"]
    pw = db_creds["password"]
    ip = db_creds["ip"]
    port = db_creds["port"]
    db = db_creds["database"]
    db_url = f"postgresql://" f"{login}:" f"{pw}@" f"{ip}:" f"{port}/" f"{db}"

    engine = create_engine(db_url)
    Base.metadata.create_all(engine)


@pytest.fixture(scope="session")
def sessionmaker(db_creds: dict) -> AsyncSessionmaker:
    sessionmaker = AsyncSessionmaker(**db_creds)
    return sessionmaker


@pytest.fixture(scope="class")
def dal(sessionmaker: AsyncSessionmaker) -> DAL:
    dal = DAL(sessionmaker)
    return dal
