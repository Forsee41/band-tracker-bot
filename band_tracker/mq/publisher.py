import json

from aio_pika import DeliveryMode, Message, connect
from aio_pika.abc import AbstractConnection

from band_tracker.mq.messages import MQMessage


class MQPublisher:
    _url: str
    _key: str
    _exchange_name: str
    _connection: AbstractConnection

    @classmethod
    async def create(
        cls: type, routing_key: str, url: str, exchange: str
    ) -> "MQPublisher":
        self = cls()
        self._key = routing_key
        self._url = url
        self._exchange_name = exchange
        self._connection = await self.connect()
        return self

    async def _connect(self) -> AbstractConnection:
        connection = await connect(self._url)
        return connection

    async def send_message(
        self,
        message: MQMessage,
        headers: dict = {},
        persistent: bool = True,
    ) -> None:
        persistence = (
            DeliveryMode.PERSISTENT if persistent else DeliveryMode.NOT_PERSISTENT
        )
        msg_body = json.dumps(message.to_dict())
        prepared_message = Message(
            bytes(msg_body, "utf-8"),
            content_type="application/json",
            headers=headers,
            type=message.type_.value,
            delivery_mode=persistence,
        )
        async with self._connection:
            channel = await self._connection.channel()
            exchange = await channel.declare_exchange(
                self._exchange_name, auto_delete=False
            )
            await exchange.publish(prepared_message, routing_key=self._key)
