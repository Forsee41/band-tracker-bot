import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from band_tracker.core.notification import Notification
from band_tracker.db.dal_base import BaseDAL
from band_tracker.db.models import (
    AdminDB,
    EventArtistDB,
    EventUserDB,
    FollowDB,
    NotificationDB,
    UserDB,
)

log = logging.getLogger(__name__)


class NotifierDAL(BaseDAL):
    async def get_admin_chats(self) -> list[str]:
        stmt = select(AdminDB)
        async with self.sessionmaker.session() as session:
            scalars = await session.scalars(stmt)
            admins_db = scalars.all()
            chats = [admin.chat_id for admin in admins_db]
            return chats

    async def _create_event_artist_notifications(
        self, event_artist: EventArtistDB, session: AsyncSession
    ) -> None:
        stmt = (
            select(UserDB)
            .join(FollowDB, FollowDB.user_id == UserDB.id)
            .where(FollowDB.artist_id == event_artist.artist_id)
            .where(FollowDB.notify.is_(True))
        )
        async with self.sessionmaker.session() as session:
            scalars = await session.scalars(stmt)
            users = scalars.all()
            for user in users:
                event_user_exists_stmt = (
                    select(EventUserDB)
                    .where(EventUserDB.event_id == event_artist.event_id)
                    .where(EventUserDB.user_id == user.id)
                )
                event_user_row = (await session.execute(event_user_exists_stmt)).first()
                if event_user_row is None:
                    event_user = EventUserDB(
                        user_id=user.id, event_id=event_artist.event_id
                    )
                    session.add(event_user)
                    await session.flush()
                else:
                    event_user = event_user_row.EventUserDB
                notification = NotificationDB(
                    event_user_id=event_user.id, artist_id=event_artist.artist_id
                )
                session.add(notification)
                try:
                    await session.flush()
                except IntegrityError:
                    log.error(
                        "Processing the same event_artist twice,"
                        " attempted creating multiple notifications!"
                    )
                    session.expunge(notification)
            await session.commit()

    async def create_notifications(self, event_uuid: UUID) -> None:
        stmt = (
            select(EventArtistDB)
            .where(EventArtistDB.event_id == event_uuid)
            .where(EventArtistDB.is_notified.is_(False))
        )
        async with self.sessionmaker.session() as session:
            scalars = await session.scalars(stmt)
            event_artists_db: list[EventArtistDB] = scalars.all()
            for event_artist in event_artists_db:
                await self._create_event_artist_notifications(event_artist, session)

    async def get_notifications(self) -> list[Notification]:
        return []

    async def confirm_notification(self, notification: Notification) -> None:
        ...
