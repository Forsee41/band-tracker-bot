from typing import Callable

import pytest

from band_tracker.core.user import User
from band_tracker.db.dal_bot import BotDAL

UserFixture = Callable[[int, str], User]


class TestGetUser:
    async def test_normal_user(self, user: UserFixture, bot_dal: BotDAL) -> None:
        user1 = user(1, "user1")
        await bot_dal.add_user(user1)
        result = await bot_dal.get_user(user1.id)
        assert result
        assert result == user1

    async def test_non_existing_user(self, user: UserFixture, bot_dal: BotDAL) -> None:
        user1 = user(1, "user1")
        await bot_dal.add_user(user1)
        result = await bot_dal.get_user(2)
        assert result is None

    async def test_multiple_users(self, user: UserFixture, bot_dal: BotDAL) -> None:
        user1 = user(1, "user1")
        user2 = user(2, "user1")
        await bot_dal.add_user(user1)
        await bot_dal.add_user(user2)
        result1 = await bot_dal.get_user(1)
        result2 = await bot_dal.get_user(2)
        assert result1 == user1
        assert result2 == user2


if __name__ == "__main__":
    pytest.main()
