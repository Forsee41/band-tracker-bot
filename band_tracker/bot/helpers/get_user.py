import logging
from datetime import datetime
from typing import Protocol

from band_tracker.core.user import RawUser, User
from band_tracker.core.user_settings import UserSettings
from band_tracker.db.dal_bot import BotDAL

log = logging.getLogger(__name__)


class TgUser(Protocol):
    id: int

    @property
    def name(self) -> str:
        ...


def default_user(user_tg: TgUser) -> RawUser:
    user_settings = UserSettings.default()
    user = RawUser(
        tg_id=int(user_tg.id),
        name=user_tg.name,
        follows={},
        join_date=datetime.now(),
        settings=user_settings,
    )
    return user


async def get_user(tg_user: TgUser, dal: BotDAL) -> User:
    """
    Returns core User for a passed tg user, or registers a new one
    and returns it if user doesn't exist.
    """
    user = await dal.get_user(tg_user.id)
    if user:
        log.debug("get_user bot helper found a user right away")
        return user
    raw_user = default_user(tg_user)
    result = await dal.add_user(raw_user)
    return result
