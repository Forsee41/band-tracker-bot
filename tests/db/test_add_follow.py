from typing import Callable

import pytest

from band_tracker.core.user import RawUser
from band_tracker.db.artist_update import ArtistUpdate
from band_tracker.db.dal_bot import BotDAL
from band_tracker.db.dal_update import UpdateDAL as DAL

UserFixture = Callable[[int, str], RawUser]


class TestAddFollowDAL:
    async def test_add_follow(
        self,
        user: UserFixture,
        bot_dal: BotDAL,
        update_dal: DAL,
        get_artist_update: Callable[[str], ArtistUpdate],
    ) -> None:
        user_1 = user(1, "user1")
        artist_update = get_artist_update("gosha")
        artist_id = await update_dal._add_artist(artist_update)
        await bot_dal.add_user(user_1)
        await bot_dal.add_follow(user_tg_id=1, artist_id=artist_id)
        user_result = await bot_dal.get_user(1)
        assert user_result
        follows = user_result.follows
        assert len(follows) == 1
        assert artist_id in follows

    async def test_add_several_follows(
        self,
        user: UserFixture,
        bot_dal: BotDAL,
        update_dal: DAL,
        get_artist_update: Callable[[str], ArtistUpdate],
    ) -> None:
        user_1 = user(1, "user1")
        artist1_update = get_artist_update("gosha")
        artist2_update = get_artist_update("clara")
        artist1_id = await update_dal._add_artist(artist1_update)
        artist2_id = await update_dal._add_artist(artist2_update)
        await bot_dal.add_user(user_1)
        await bot_dal.add_follow(user_tg_id=1, artist_id=artist1_id)
        await bot_dal.add_follow(user_tg_id=1, artist_id=artist2_id)
        user_result = await bot_dal.get_user(1)
        assert user_result
        follows = user_result.follows
        assert len(follows) == 2
        assert artist1_id in follows
        assert artist2_id in follows

    async def test_remove_follow(
        self,
        user: UserFixture,
        bot_dal: BotDAL,
        update_dal: DAL,
        get_artist_update: Callable[[str], ArtistUpdate],
    ) -> None:
        user_1 = user(1, "user1")
        artist_update = get_artist_update("gosha")
        artist_id = await update_dal._add_artist(artist_update)
        await bot_dal.add_user(user_1)
        await bot_dal.add_follow(user_tg_id=1, artist_id=artist_id)
        await bot_dal.unfollow(user_tg_id=1, artist_id=artist_id)
        user_result = await bot_dal.get_user(1)
        assert user_result
        follows = user_result.follows
        assert len(follows) == 0

    async def test_right_follow_removed(
        self,
        user: UserFixture,
        bot_dal: BotDAL,
        update_dal: DAL,
        get_artist_update: Callable[[str], ArtistUpdate],
    ) -> None:
        user_1 = user(1, "user1")
        artist1_update = get_artist_update("gosha")
        artist2_update = get_artist_update("clara")
        artist1_id = await update_dal._add_artist(artist1_update)
        artist2_id = await update_dal._add_artist(artist2_update)
        await bot_dal.add_user(user_1)
        await bot_dal.add_follow(user_tg_id=1, artist_id=artist1_id)
        await bot_dal.add_follow(user_tg_id=1, artist_id=artist2_id)
        await bot_dal.unfollow(user_tg_id=1, artist_id=artist1_id)
        user_result = await bot_dal.get_user(1)
        assert user_result
        follows = user_result.follows
        assert len(follows) == 1
        assert artist1_id not in follows
        assert artist2_id in follows

    async def test_refollow(
        self,
        user: UserFixture,
        bot_dal: BotDAL,
        update_dal: DAL,
        get_artist_update: Callable[[str], ArtistUpdate],
    ) -> None:
        user_1 = user(1, "user1")
        artist_update = get_artist_update("gosha")
        artist_id = await update_dal._add_artist(artist_update)
        await bot_dal.add_user(user_1)
        await bot_dal.add_follow(user_tg_id=1, artist_id=artist_id)
        await bot_dal.unfollow(user_tg_id=1, artist_id=artist_id)
        await bot_dal.add_follow(user_tg_id=1, artist_id=artist_id)
        user_result = await bot_dal.get_user(1)
        assert user_result
        follows = user_result.follows
        assert len(follows) == 1
        assert artist_id in follows


if __name__ == "__main__":
    pytest.main()
