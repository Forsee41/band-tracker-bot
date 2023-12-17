from typing import Callable

from band_tracker.config.constants import NO_DELETE
from band_tracker.core.enums import MessageType
from band_tracker.core.user import RawUser
from band_tracker.db.dal_bot import BotDAL
from band_tracker.db.dal_message import MessageDAL

UserFixture = Callable[[int, str], RawUser]


async def test_clean_works(
    message_dal: MessageDAL, user: UserFixture, bot_dal: BotDAL
) -> None:
    user1 = user(1, "user")
    added_user = await bot_dal.add_user(user1)

    await message_dal.register_message(
        message_type=MessageType.AMP, user_id=added_user.id, message_tg_id=3
    )
    await message_dal.register_message(
        message_type=MessageType.AMP, user_id=added_user.id, message_tg_id=4
    )
    result = await message_dal.delete_user_messages(
        user_id=added_user.id, no_delete=NO_DELETE
    )
    assert len(result) == 2
    assert 3 in result
    assert 4 in result


async def test_notifications_not_deleted(
    message_dal: MessageDAL, user: UserFixture, bot_dal: BotDAL
) -> None:
    user1 = user(1, "user")
    added_user = await bot_dal.add_user(user1)

    await message_dal.register_message(
        message_type=MessageType.AMP, user_id=added_user.id, message_tg_id=3
    )
    await message_dal.register_message(
        message_type=MessageType.NOTIFICATION, user_id=added_user.id, message_tg_id=4
    )
    result = await message_dal.delete_user_messages(
        user_id=added_user.id, no_delete=NO_DELETE
    )
    assert len(result) == 1
    assert 3 in result
    assert 4 not in result


async def test_test_not_deleted(
    message_dal: MessageDAL, user: UserFixture, bot_dal: BotDAL
) -> None:
    user1 = user(1, "user")
    added_user = await bot_dal.add_user(user1)

    await message_dal.register_message(
        message_type=MessageType.AMP, user_id=added_user.id, message_tg_id=3
    )
    await message_dal.register_message(
        message_type=MessageType.TEST, user_id=added_user.id, message_tg_id=4
    )
    result = await message_dal.delete_user_messages(
        user_id=added_user.id, no_delete=NO_DELETE
    )
    assert len(result) == 1
    assert 3 in result
    assert 4 not in result


async def test_works_with_multiple_users(
    message_dal: MessageDAL, user: UserFixture, bot_dal: BotDAL
) -> None:
    user1 = user(1, "user")
    added_user1 = await bot_dal.add_user(user1)
    user2 = user(2, "user")
    added_user2 = await bot_dal.add_user(user2)

    await message_dal.register_message(
        message_type=MessageType.AMP, user_id=added_user1.id, message_tg_id=3
    )
    await message_dal.register_message(
        message_type=MessageType.AMP, user_id=added_user2.id, message_tg_id=4
    )
    result = await message_dal.delete_user_messages(
        user_id=added_user1.id, no_delete=NO_DELETE
    )
    assert len(result) == 1
    assert 3 in result
    assert 4 not in result
