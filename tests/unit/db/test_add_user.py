from typing import Callable

import pytest

from band_tracker.core.user import User
from band_tracker.db.dal_bot import BotDAL
from band_tracker.db.errors import UserAlreadyExists

UserFixture = Callable[[int, str], User]


class TestAddUser:
    async def test_add_same_user_fails(
        self, user: UserFixture, bot_dal: BotDAL
    ) -> None:
        user1 = user(1, "user1")
        user2 = user(1, "user1")
        await bot_dal.add_user(user1)
        with pytest.raises(UserAlreadyExists) as e:
            await bot_dal.add_user(user2)
            assert e


if __name__ == "__main__":
    pytest.main()
