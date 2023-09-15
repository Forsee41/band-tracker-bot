import os

import asyncio
from telegram import Bot


class Notifier:
    def __init__(self, bot: Bot, admin_chats: list[int]) -> None:
        self.bot = bot
        self.admin_chats = admin_chats

    async def notify_admins(self, text: str) -> None:
        for admin_chat_id in self.admin_chats:
            await self.bot.sendMessage(chat_id=admin_chat_id, text=text)


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    bot = Bot(token=token)
    asyncio.run(bot.sendMessage(chat_id=986579738, text="Hi!!!!!!!!!"))
