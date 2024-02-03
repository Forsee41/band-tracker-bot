import logging
from uuid import UUID

from sqlalchemy import select

from band_tracker.core.notification import Notification
from band_tracker.db.dal_base import BaseDAL
from band_tracker.db.models import AdminDB

log = logging.getLogger(__name__)


class NotifierDAL(BaseDAL):
    async def get_admin_chats(self) -> list[str]:
        stmt = select(AdminDB)
        async with self.sessionmaker.session() as session:
            scalars = await session.scalars(stmt)
            admins_db = scalars.all()
            chats = [admin.chat_id for admin in admins_db]
            return chats

    async def create_notifications(self, uuid: UUID) -> None:
        ...

    async def get_notifications(self) -> list[Notification]:
        return []
        ...

    async def confirm_notification(self, notification: Notification) -> None:
        ...
