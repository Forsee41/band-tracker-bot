import asyncio
import json

from aio_pika import ExchangeType, connect
from aio_pika.abc import AbstractConnection, AbstractIncomingMessage
from telegram import Bot

from band_tracker.db.dal import BotDAL


class Notifier:
    bot: Bot
    mq_routing_key: str
    mq_connection: AbstractConnection
    mq_exchange_name: str
    dal: BotDAL

    @classmethod
    async def create(
        cls: type,
        bot: "Bot",
        mq_url: str,
        mq_routing_key: str,
        exchange_name: str,
        dal: BotDAL,
    ) -> "Notifier":
        self: "Notifier" = cls()
        self.dal = dal
        self.bot = bot
        self.mq_routing_key = mq_routing_key
        self.mq_exchange_name = exchange_name
        self.mq_connection = await connect(mq_url)
        return self

    async def consume(self) -> None:
        connection = self.mq_connection
        async with connection:
            channel = await connection.channel()

            exchange = await channel.declare_exchange(
                self.mq_exchange_name, ExchangeType.DIRECT
            )
            queue = await channel.declare_queue("notifier_queue")
            await queue.bind(exchange, self.mq_routing_key)
            await queue.consume(self.on_message)
            await asyncio.Future()

    async def notify_admins(self, text: str) -> None:
        admin_chats = await self.dal.get_admin_chats()
        for admin_chat_id in admin_chats:
            await self.bot.sendMessage(chat_id=admin_chat_id, text=text)  # type: ignore

    async def on_message(self, message: AbstractIncomingMessage) -> None:
        async with message.process():
            msg_raw = message.body.decode()
            msg = json.loads(msg_raw)
            match message.type:
                case "notification":
                    await self.notify_admins(text=msg["message"])
