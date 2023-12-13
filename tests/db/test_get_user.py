from typing import Callable

import pytest

from band_tracker.core.user import RawUser
from band_tracker.db.dal_bot import BotDAL

UserFixture = Callable[[int, str], RawUser]


class TestGetUser:
    async def test_normal_user(self, user: UserFixture, bot_dal: BotDAL) -> None:
        user1 = user(1, "user1")
        added = await bot_dal.add_user(user1)
        result = await bot_dal.get_user(user1.tg_id)
        assert result
        assert result == added

    async def test_non_existing_user(self, user: UserFixture, bot_dal: BotDAL) -> None:
        user1 = user(1, "user1")
        await bot_dal.add_user(user1)
        result = await bot_dal.get_user(2)
        assert result is None

    async def test_multiple_users(self, user: UserFixture, bot_dal: BotDAL) -> None:
        user1 = user(1, "user1")
        user2 = user(2, "user1")
        added1 = await bot_dal.add_user(user1)
        added2 = await bot_dal.add_user(user2)
        result1 = await bot_dal.get_user(1)
        result2 = await bot_dal.get_user(2)
        assert result1 == added1
        assert result2 == added2


if __name__ == "__main__":
    pytest.main()
