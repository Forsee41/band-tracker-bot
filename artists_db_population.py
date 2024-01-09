import asyncio
import logging
import os
import sys

from dotenv import load_dotenv

from band_tracker.config.env_loader import db_env_vars, events_api_env_vars
from band_tracker.config.log import load_log_config
from band_tracker.db.dal_update import UpdateDAL
from band_tracker.db.session import AsyncSessionmaker
from band_tracker.updater.updater import ClientFactory, Updater

log = logging.getLogger(__name__)


async def main() -> None:
    events_env = events_api_env_vars()
    db_env = db_env_vars()
    load_log_config()

    tokens = events_env.CONCERTS_API_TOKENS

    db_sessionmaker = AsyncSessionmaker(
        login=db_env.DB_LOGIN,
        password=db_env.DB_PASSWORD,
        ip=db_env.DB_IP,
        port=db_env.DB_PORT,
        database=db_env.DB_NAME,
    )
    dal = UpdateDAL(db_sessionmaker)

    """num_coroutines = 4
    if num_coroutines > len(tokens):
        log.warning(
            "The number of tokens should be at least equal to the number of coroutines"
        )

    number_of_artists = 10000
    chunk_size = ceil((end_index - start_index) / num_coroutines)

    tokens_blocks = [
        tokens[i: i + len(tokens) // num_coroutines]
        for i in range(0, len(tokens), len(tokens) // num_coroutines)
    ]

    tasks = []
    for i, start in enumerate(range(start_index, end_index, chunk_size + 1)):
        end = min(start + chunk_size, end_index)
        api_client_factory = ClientFactory(
            base_url=events_env.CONCERTS_API_URL, tokens=tokens_blocks[i]
        )
        updater = Updater(
            client_factory=api_client_factory,
            dal=dal,
        )
        chunk_processer = ArtistDbPopulation(start, end, updater)
        task = asyncio.create_task(chunk_processer.process_subrange())
        tasks.append(task)
    await asyncio.gather(*tasks)"""

    api_client_factory = ClientFactory(
        base_url=events_env.CONCERTS_API_URL, tokens=tokens
    )
    updater = Updater(
        client_factory=api_client_factory,
        dal=dal,
    )
    artist_names: list[str] = await dal.get_all_artist_names()
    await updater.update_artists(artist_names)
    log.info("!!!!!!!!!!!!!!!! Artists population close !!!!!!!!!!!!!!!!")


if __name__ == "__main__":
    load_dotenv()
    sys.path.append(os.getcwd())
    asyncio.run(main())
