import asyncio
import logging
import os
import sys

from dotenv import load_dotenv

from band_tracker.config.log import load_log_config
from band_tracker.db.artist_update import get_description

log = logging.getLogger(__name__)


async def main() -> None:
    load_log_config()

    response = await get_description(
        "https://en.wikipedia.org/wiki/Death_Grips", key_words={"death grips", "boba"}
    )
    log.info(response)


if __name__ == "__main__":
    load_dotenv()
    sys.path.append(os.getcwd())
    asyncio.run(main())
