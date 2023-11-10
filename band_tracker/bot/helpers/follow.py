import logging
from uuid import UUID

from band_tracker.db.dal_bot import BotDAL
from band_tracker.db.errors import ArtistNotFound, UserNotFound

log = logging.getLogger(__name__)


async def add_follow(dal: BotDAL, user_id: int, artist_id: UUID) -> None:
    try:
        await dal.add_follow(user_tg_id=user_id, artist_id=artist_id)
    except ArtistNotFound:
        log.warning("Can't create a follow, artist is not present in db")
    except UserNotFound:
        log.warning("Can't create a follow, user is not present in db")
