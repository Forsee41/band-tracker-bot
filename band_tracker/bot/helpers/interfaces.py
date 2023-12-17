import asyncio
from collections.abc import Awaitable

from telegram import Bot, InlineKeyboardMarkup

from band_tracker.core.enums import MessageType
from band_tracker.core.user import User
from band_tracker.db.dal_message import MessageDAL


class MessageManager:
    def __init__(
        self, msg_dal: MessageDAL, bot: Bot, no_delete: list[MessageType]
    ) -> None:
        self.dal = msg_dal
        self.bot = bot
        self._no_delete = no_delete

    async def delete_messages(self, msg_ids: list[int], chat_id: int) -> None:
        tasks: list[Awaitable] = []
        for id in msg_ids:
            task = self.bot.delete_message(
                message_id=id, chat_id=chat_id
            )  # type: ignore
            tasks.append(task)
        await asyncio.gather(*tasks)

    async def send_text(
        self,
        text: str,
        markup: InlineKeyboardMarkup | None,
        user: User,
        msg_type: MessageType,
        delete_prev: bool = True,
    ) -> None:
        if delete_prev:
            old_ids = await self.dal.delete_user_messages(
                user_id=user.id, no_delete=self._no_delete
            )
            await self.delete_messages(msg_ids=old_ids, chat_id=user.tg_id)
        msg = await self.bot.send_message(
            text=text,
            reply_markup=markup,
            chat_id=user.tg_id,
            parse_mode="HTML",
        )  # type: ignore
        await self.dal.register_message(
            message_type=msg_type, user_id=user.id, message_tg_id=msg.id
        )

    async def send_image(
        self,
        text: str,
        markup: InlineKeyboardMarkup | None,
        user: User,
        image: str,
        msg_type: MessageType,
        delete_prev: bool = True,
    ) -> None:
        if delete_prev:
            old_ids = await self.dal.delete_user_messages(
                user_id=user.id, no_delete=self._no_delete
            )
            await self.delete_messages(msg_ids=old_ids, chat_id=user.tg_id)
        msg = await self.bot.send_photo(
            caption=text,
            reply_markup=markup,
            chat_id=user.tg_id,
            photo=image,
            parse_mode="HTML",
        )  # type: ignore
        await self.dal.register_message(
            message_type=msg_type,
            user_id=user.id,
            message_tg_id=msg.id,
        )
