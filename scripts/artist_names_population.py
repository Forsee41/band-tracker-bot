import asyncio
import logging
import os
import sys

import httpx
from dotenv import load_dotenv

from band_tracker.config.env_loader import db_env_vars, events_api_env_vars
from band_tracker.config.log import load_log_config
from band_tracker.db.dal_update import UpdateDAL
from band_tracker.db.session import AsyncSessionmaker
from band_tracker.updater.errors import InvalidResponseStructureError


async def main() -> None:
    load_log_config()
    log = logging.getLogger(__name__)

    load_dotenv()
    events_env = events_api_env_vars()
    db_env = db_env_vars()

    db_sessionmaker = AsyncSessionmaker(
        login=db_env.DB_LOGIN,
        password=db_env.DB_PASSWORD,
        ip=db_env.DB_IP,
        port=db_env.DB_PORT,
        database=db_env.DB_NAME,
    )
    dal = UpdateDAL(db_sessionmaker)

    base_url = events_env.SEATGEEK_URL
    api_token = events_env.SEATGEEK_TOKEN
    params = {"client_id": api_token, "taxonomies.id": "2000000", "per_page": 5000}
    log.debug(
        "---------------------------------------------Population script "
        "start---------------------------------------------"
    )
    page = 0

    while True:
        page += 1
        params.update({"page": str(page)})
        raw_dict = httpx.get(base_url, params=params).json()

        if "performers" not in raw_dict:
            raise InvalidResponseStructureError
        performers = raw_dict.get("performers", {})
        if performers:
            for artist in performers:
                name = artist.get("name")
                await dal.add_external_artist_name(name)
        else:
            log.info(
                "script stopped working due to empty performers list in the responded page"
            )
            break


if __name__ == "__main__":
    load_dotenv()
    sys.path.append(os.getcwd())
    asyncio.run(main())
