import asyncio
from collections.abc import Awaitable

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

from band_tracker.core.enums import MessageType
from band_tracker.core.notification import Notification
from band_tracker.core.user import User
from band_tracker.db.dal_message import MessageDAL
from band_tracker.db.errors import DALError


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

    def _create_notification_text(self, notification: Notification) -> str:
        new_artists_str = ", ".join(
            [artist.name for artist in notification.target_artists]
        )
        result = f"!!! {notification.event.title} !!!\n"
        result += f"{new_artists_str} going to be there!"
        date_str = notification.event.date.strftime("%d/%m/%Y")
        result += f"Starts at {date_str}"
        return result

    async def send_notification(self, notification: Notification) -> None:
        text = self._create_notification_text(notification)
        callback_data = f"event {notification.event.id}"
        button = InlineKeyboardButton(
            text=notification.event.title, callback_data=callback_data
        )
        markup = InlineKeyboardMarkup([[button]])
        user = await self.dal.get_user_by_uuid(notification.user.id)
        if user is None:
            raise DALError("Can't find user!")
        await self.send_text(
            text=text,
            markup=markup,
            user=user,
            msg_type=MessageType.NOTIFICATION,
            delete_prev=False,
        )
