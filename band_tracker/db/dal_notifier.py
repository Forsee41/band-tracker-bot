import logging
from collections import defaultdict
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from band_tracker.core.artist import Artist
from band_tracker.core.event import Event
from band_tracker.core.notification import Notification
from band_tracker.core.user import User
from band_tracker.db.dal_base import BaseDAL
from band_tracker.db.errors import DALError
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
                await session.commit()

    def _split_event_notifications_by_users(
        self, notifications: list[NotificationDB]
    ) -> dict[UUID, list[NotificationDB]]:
        result: dict[UUID, list[NotificationDB]] = defaultdict(list)
        for notification in notifications:
            result[notification.event_user.user_id].append(notification)
        return result

    async def _populate_with_other_artists(
        self, notification: Notification, session: AsyncSession
    ) -> Notification:
        # TODO
        assert session
        return notification

    async def _generate_notification(
        self,
        user: User,
        event: Event,
        db_notifications: list[NotificationDB],
        is_new: bool,
        session: AsyncSession,
    ) -> Notification:
        artist_ids = [notification.artist_id for notification in db_notifications]
        artists: list[Artist] = []
        for artist_id in artist_ids:
            artist = await self._get_artist(artist_id, session)
            if artist is not None:
                artists.append(artist)

        notification = Notification(
            event,
            user,
            artists,
            [],
            is_new,
        )
        notification = await self._populate_with_other_artists(notification, session)
        return notification

    async def _get_event_notifications_by_group(
        self, event: Event, is_event_user_notified: bool, session: AsyncSession
    ) -> list[Notification]:
        result: list[Notification] = []
        stmt = (
            select(NotificationDB)
            .join(EventUserDB, EventUserDB.id == NotificationDB.event_user_id)
            .where(EventUserDB.is_notified.is_(is_event_user_notified))
            .where(NotificationDB.is_notified.is_(False))
            .where(EventUserDB.event_id == event.id)
            .options(selectinload(NotificationDB.event_user))
        )
        scalars = await session.scalars(stmt)
        event_notifications = list(scalars.all())
        user_new_event_notifications = self._split_event_notifications_by_users(
            event_notifications
        )
        for (
            user_uuid,
            user_db_notifications,
        ) in user_new_event_notifications.items():
            user = await self.get_user_by_uuid(user_uuid)
            if user is None:
                raise DALError("Trying to get user with not existing uuid")
            notification = await self._generate_notification(
                user, event, user_db_notifications, not is_event_user_notified, session
            )
            result.append(notification)
        return result

    async def get_event_notifications(self, event_uuid: UUID) -> list[Notification]:
        result: list[Notification] = []
        async with self.sessionmaker.session() as session:
            event = await self.get_event(event_uuid)
            if event is None:
                raise DALError("Couldn't get requested event!")

            already_notified = await self._get_event_notifications_by_group(
                event, True, session
            )
            new = await self._get_event_notifications_by_group(event, False, session)

            result.extend(already_notified)
            result.extend(new)
        return result

    async def confirm_notification(self, notification: Notification) -> None:
        event_user_query = (
            select(EventUserDB)
            .where(EventUserDB.event_id == notification.event.id)
            .where(EventUserDB.user_id == notification.user.id)
        )
        new_artist_ids = [artist.id for artist in notification.target_artists]
        notifications_query = (
            select(NotificationDB)
            .join(EventUserDB, NotificationDB.event_user_id == EventUserDB.id)
            .where(NotificationDB.artist_id.in_(new_artist_ids))
            .where(EventUserDB.user_id == notification.user.id)
            .where(EventUserDB.event_id == notification.event.id)
        )
        async with self.sessionmaker.session() as session:
            scalars = await session.scalars(event_user_query)
            event_user = scalars.first()
            if event_user is None:
                raise DALError("Couldn't find an event user for notification")
            event_user.is_notified = True
            session.add(event_user)
            scalars = await session.scalars(notifications_query)
            notifications_db: list[NotificationDB] = scalars.all()
            for notification_db in notifications_db:
                notification_db.is_notified = True
                session.add(notification_db)
            await session.commit()
