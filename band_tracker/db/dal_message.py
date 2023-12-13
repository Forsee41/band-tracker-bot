import logging
from uuid import UUID

from sqlalchemy import select

from band_tracker.core.enums import MessageType
from band_tracker.db.dal_base import BaseDAL
from band_tracker.db.models import MessageDB, UserDB

log = logging.getLogger(__name__)


class MessageDAL(BaseDAL):
    async def register_message(
        self, message_type: MessageType, user_id: UUID, message_tg_id: int
    ) -> UUID:
        message = MessageDB(
            message_type=message_type, user_id=user_id, tg_message_id=message_tg_id
        )
        async with self.sessionmaker.session() as session:
            session.add(message)
            await session.flush()
            message_id = message.id
            await session.commit()
        return message_id

    async def delete_user_messages(self, user_id: UUID) -> list[int]:
        """
        Marks all active interfaces for a user as inactive and returns their tg ids.
        """
        stmt = (
            select(MessageDB)
            .join(UserDB, UserDB.id == MessageDB.user_id)
            .where(UserDB.id == user_id)
            .where(MessageDB.active)
            .where(
                MessageDB.message_type.not_in(
                    [MessageType.NOTIFICATION, MessageType.TEST]
                )
            )
        )
        async with self.sessionmaker.session() as session:
            scalars = await session.scalars(stmt)
            messages: list[MessageDB] = scalars.all()
            message_ids = [message.tg_message_id for message in messages]
            for message in messages:
                message.active = False
            session.add_all(messages)
            await session.commit()
        return message_ids
