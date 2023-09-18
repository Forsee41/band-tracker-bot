import asyncio

from aio_pika import ExchangeType, connect
from aio_pika.abc import AbstractConnection, AbstractIncomingMessage
from telegram import Bot


class Notifier:
    bot: Bot
    admin_chats: list[int]
    mq_routing_key: str
    mq_connection: AbstractConnection
    mq_exchange_name: str

    @classmethod
    async def create(
        cls: type,
        bot: Bot,
        admin_chats: list[int],
        mq_url: str,
        mq_routing_key: str,
        exchange_name: str,
    ) -> "Notifier":
        self = cls()
        self.bot = bot
        self.admin_chats = admin_chats
        self.mq_url = mq_url
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
        for admin_chat_id in self.admin_chats:
            await self.bot.sendMessage(chat_id=admin_chat_id, text=text)

    async def on_message(self, message: AbstractIncomingMessage) -> None:
        async with message.process():
            print(f"Received message: {message.body.decode()}")
