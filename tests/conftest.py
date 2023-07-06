import os

import pytest
from dotenv import load_dotenv

from band_tracker.db.dal import DAL
from band_tracker.db.session import AsyncSessionmaker


@pytest.fixture(scope="session")
def load_dotenv_() -> None:
    load_dotenv()


@pytest.fixture(scope="session")
def db_creds(load_dotenv_) -> dict:
    assert load_dotenv_ is None
    db_creds = {
        "login": os.getenv("TEST_DB_LOGIN"),
        "password": os.getenv("TEST_DB_PASSWORD"),
        "ip": os.getenv("TEST_DB_IP"),
        "port": os.getenv("TEST_DB_PORT"),
        "database": os.getenv("TEST_DB_NAME"),
    }
    return db_creds


@pytest.fixture(scope="session")
def sessionmaker(db_creds: dict) -> AsyncSessionmaker:
    sessionmaker = AsyncSessionmaker(**db_creds)
    return sessionmaker


@pytest.fixture(scope="class")
def dal(sessionmaker: AsyncSessionmaker) -> DAL:
    dal = DAL(sessionmaker)
    return dal
