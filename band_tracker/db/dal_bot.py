import logging
import re
from uuid import UUID

from sqlalchemy import desc, func, literal, select
from sqlalchemy.orm import joinedload, selectinload

from band_tracker.core.artist import Artist
from band_tracker.core.enums import AdminNotificationLevel
from band_tracker.core.event import Event
from band_tracker.core.user import User
from band_tracker.db.dal_base import BaseDAL
from band_tracker.db.models import AdminDB, ArtistAliasDB, ArtistDB, EventDB

log = logging.getLogger(__name__)


class BotDAL(BaseDAL):
    async def search_artist(
        self, search_str: str, similarity_min: float = 0.3
    ) -> list[Artist]:
        log.debug("In search artist")

        sanitized_search_str = re.sub(r"\W+", "", search_str)
        max_similarity = func.max(
            func.similarity(ArtistAliasDB.alias, literal(sanitized_search_str))
        ).label("max_similarity")
        subquery = (
            select(ArtistDB.id, max_similarity)
            .join(ArtistAliasDB, ArtistDB.id == ArtistAliasDB.artist_id)
            .filter(
                func.similarity(ArtistAliasDB.alias, literal(sanitized_search_str))
                > similarity_min
            )
            .group_by(ArtistDB.id)
            .order_by(max_similarity.desc())
            .subquery()
        )
        stmt = (
            select(ArtistDB)
            .join(subquery, ArtistDB.id == subquery.c.id)
            .order_by(desc(subquery.c.max_similarity))
            .limit(10)
            .options(joinedload(ArtistDB.socials))
            .options(selectinload(ArtistDB.genres))
        )
        async with self.sessionmaker.session() as session:
            scalars = await session.scalars(stmt)
            artists = scalars.all()
            if artists:
                log.debug(f"First artist genres: {artists[0].genres}")
            return [
                self._build_core_artist(
                    db_artist=artist, db_socials=artist.socials, genres=artist.genres
                )
                for artist in artists
            ]

    async def get_artist_by_name(self, name: str) -> Artist | None:
        stmt = (
            select(ArtistDB)
            .where(ArtistDB.name == name)
            .options(joinedload(ArtistDB.socials))
            .options(selectinload(ArtistDB.genres))
        )
        async with self.sessionmaker.session() as session:
            scalars = await session.scalars(stmt)
            artist = scalars.first()
        if artist is None:
            return None
        return self._build_core_artist(
            db_artist=artist, db_socials=artist.socials, genres=artist.genres
        )

    async def add_admin(
        self,
        name: str,
        chat_id: str,
        notification_level: AdminNotificationLevel = AdminNotificationLevel.INFO,
    ) -> None:
        async with self.sessionmaker.session() as session:
            admin = AdminDB(
                name=name, notification_level=notification_level, chat_id=chat_id
            )
            session.add(admin)
            await session.commit()

    async def get_admin_chats(self) -> list[str]:
        stmt = select(AdminDB)
        async with self.sessionmaker.session() as session:
            scalars = await session.scalars(stmt)
            admins_db = scalars.all()
            chats = [admin.chat_id for admin in admins_db]
            return chats

    async def get_event(self, id: UUID) -> Event | None:
        stmt = select(EventDB).where(EventDB.id == id)
        async with self.sessionmaker.session() as session:
            scalars = await session.scalars(stmt)
            event_db = scalars.first()
            if event_db is None:
                return None
            sales_result = await event_db.awaitable_attrs.sales
            sales_db = sales_result[0]
            artists = await event_db.awaitable_attrs.artists
            artist_ids = [artist.id for artist in artists]

            event = self._build_core_event(event_db, sales_db, artist_ids)
            return event

    async def get_artist(self, id: UUID) -> Artist | None:
        stmt = (
            select(ArtistDB)
            .where(ArtistDB.id == id)
            .options(joinedload(ArtistDB.genres))
        )
        async with self.sessionmaker.session() as session:
            scalars = await session.scalars(stmt)
            artist_db = scalars.first()
            if artist_db is None:
                return None
            socials_db_result = await artist_db.awaitable_attrs.socials
            socials_db = socials_db_result

        artist = self._build_core_artist(
            db_artist=artist_db, db_socials=socials_db, genres=artist_db.genres
        )
        return artist

    async def add_user(self, user: User) -> None:
        async with self.sessionmaker.session() as session:
            user_db = self._core_to_db_user(user)
            session.add(user_db)
            session.commit()
