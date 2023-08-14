import asyncio

from dotenv import load_dotenv

from band_tracker.config.env_loader import db_env_vars, events_api_env_vars
from band_tracker.db.dal import UpdateDAL
from band_tracker.db.session import AsyncSessionmaker
from band_tracker.updater.updater import ClientFactory, Updater


def main() -> None:
    load_dotenv()

    events_env = events_api_env_vars()
    db_env = db_env_vars()
    api_client_factory = ClientFactory(
        url=events_env.EVENTS_API_URL, token=events_env.EVENTS_API_LOGIN
    )
    db_sessionmaker = AsyncSessionmaker(
        login=db_env.DB_LOGIN,
        password=db_env.DB_PASSWORD,
        ip=db_env.DB_IP,
        port=db_env.DB_PORT,
        database=db_env.DB_NAME,
    )
    dal = UpdateDAL(db_sessionmaker)
    updater = Updater(client_factory=api_client_factory, dal=dal)
    asyncio.run(updater.update_artists())
