import asyncio
import logging
import os
import sys
from math import ceil

import asyncpg
from asyncpg import Pool
from dotenv import load_dotenv

from band_tracker.config.env_loader import db_env_vars, events_api_env_vars
from band_tracker.config.log import load_log_config
from band_tracker.db.dal_update import UpdateDAL
from band_tracker.db.session import AsyncSessionmaker
from band_tracker.updater.updater import ClientFactory, Updater

log = logging.getLogger(__name__)


class ArtistDbPopulation:
    def __init__(self, start, end, updater, db_pool):
        self.start = start
        self.end = end
        self.updater = updater
        self.db_pool = db_pool

    async def process_subrange(self):
        async with self.db_pool.acquire() as connection:
            select_query = "SELECT id, name FROM artists WHERE id BETWEEN $1 AND $2"
            update_query = "UPDATE artists SET checked = true WHERE id = any($1::int[])"

            result = await connection.fetch(select_query, self.start, self.end)
            db_artists = {}
            for record in result:
                db_artists.update({record["id"]: record["name"]})

            await self.updater.update_artists(db_artists)
            checked_ids = db_artists.keys()

            await connection.execute(update_query, checked_ids)


async def init_db(db_pool: Pool) -> None:
    query = "UPDATE artists SET checked = false;"
    await db_pool.execute(query)


async def main() -> None:
    events_env = events_api_env_vars()
    db_env = db_env_vars()
    load_log_config()

    user = os.getenv("ARTISTS_DB_LOGIN")
    password = os.getenv("ARTISTS_DB_PASSWORD")
    host = os.getenv("ARTISTS_DB_IP")
    port = os.getenv("ARTISTS_DB_PORT")
    database = os.getenv("ARTISTS_DB_NAME")
    db_params = {
        "host": host,
        "port": port,
        "database": database,
        "user": user,
        "password": password,
    }

    tokens = os.getenv("CONCERTS_API_TOKENS").split(",")
    db_pool = await asyncpg.create_pool(**db_params, max_size=5000)

    if len(sys.argv) > 1 and sys.argv[1] == "-init":
        await init_db(db_pool)

    db_sessionmaker = AsyncSessionmaker(
        login=db_env.DB_LOGIN,
        password=db_env.DB_PASSWORD,
        ip=db_env.DB_IP,
        port=db_env.DB_PORT,
        database=db_env.DB_NAME,
    )
    dal = UpdateDAL(db_sessionmaker)

    num_coroutines = 4
    if num_coroutines > len(tokens):
        log.warning(
            "The number of tokens should be at least equal to the number of coroutines"
        )

    start_index = 0
    end_index = 15000
    chunk_size = ceil((end_index - start_index) / num_coroutines)

    tokens_blocks = [
        tokens[i : i + len(tokens) // num_coroutines]
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
        chunk_processer = ArtistDbPopulation(start, end, updater, db_pool)
        task = asyncio.create_task(chunk_processer.process_subrange())
        tasks.append(task)
    await asyncio.gather(*tasks)

    log.info("!!!!!!!!!!!!!!!! Artists population close !!!!!!!!!!!!!!!!")
    await db_pool.close()


if __name__ == "__main__":
    load_dotenv()
    sys.path.append(os.getcwd())
    asyncio.run(main())
