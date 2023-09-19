import asyncio
import logging

from dotenv import load_dotenv

from band_tracker.config.env_loader import db_env_vars, events_api_env_vars
from band_tracker.config.log import load_log_config
from band_tracker.db.dal import UpdateDAL
from band_tracker.db.session import AsyncSessionmaker
from band_tracker.updater.updater import ClientFactory, Updater


def main() -> None:
    load_log_config()
    log = logging.getLogger(__name__)

    load_dotenv()
    events_env = events_api_env_vars()
    db_env = db_env_vars()
    api_client_factory = ClientFactory(
        base_url=events_env.CONCERTS_API_URL, token=events_env.CONCERTS_API_TOKEN
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
    log.debug(
        "---------------------------------------------Updater "
        "start---------------------------------------------"
    )
    asyncio.run(updater.update_artists())


if __name__ == "__main__":
    main()
