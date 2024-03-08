import logging
import re
from uuid import UUID

from sqlalchemy import ScalarResult, desc, func, literal, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload, selectinload

from band_tracker.core.artist import Artist
from band_tracker.core.enums import AdminNotificationLevel, Range
from band_tracker.core.event import Event
from band_tracker.core.user import RawUser, User
from band_tracker.db.dal_base import BaseDAL
from band_tracker.db.errors import ArtistNotFound, UserAlreadyExists, UserNotFound
from band_tracker.db.models import (
    AdminDB,
    ArtistAliasDB,
    ArtistDB,
    EventArtistDB,
    EventDB,
    FollowDB,
    UserDB,
)

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
            return [self._build_core_artist(db_artist=artist) for artist in artists]

    async def get_events_for_user(
        self, user_tg_id: int, page: int = 0, events_per_page: int = 5
    ) -> list[Event]:
        stmt = (
            select(EventDB)
            .join(EventArtistDB, EventDB.id == EventArtistDB.event_id)
            .join(FollowDB, FollowDB.artist_id == EventArtistDB.artist_id)
            .join(UserDB, UserDB.id == FollowDB.user_id)
            .where(UserDB.tg_id == user_tg_id)
            .where(FollowDB.active)
            .options(selectinload(EventDB.sales))
            .options(selectinload(EventDB.artists))
            .order_by(EventDB.id)
            .limit(events_per_page)
            .offset(page * events_per_page)
        )
        async with self.sessionmaker.session() as session:
            scalars = await session.scalars(stmt)
            query_results = scalars.all()

        return [self._build_core_event(event) for event in query_results]

    async def get_user_events_amount(self, user_tg_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(EventDB)
            .join(EventArtistDB, EventDB.id == EventArtistDB.event_id)
            .join(FollowDB, FollowDB.artist_id == EventArtistDB.artist_id)
            .join(UserDB, UserDB.id == FollowDB.user_id)
            .where(UserDB.tg_id == user_tg_id)
            .where(FollowDB.active)
        )
        async with self.sessionmaker.session() as session:
            result = await session.scalar(stmt)
        return result

    async def get_events_for_artist(
        self, artist_id: UUID, page: int, events_per_page: int = 5
    ) -> list[Event]:
        stmt = (
            select(EventDB)
            .join(EventArtistDB, EventDB.id == EventArtistDB.event_id)
            .options(selectinload(EventDB.sales))
            .options(selectinload(EventDB.artists))
            .where(EventArtistDB.artist_id == artist_id)
            .order_by(EventDB.id)
            .limit(events_per_page)
            .offset(page * events_per_page)
        )
        async with self.sessionmaker.session() as session:
            scalars = await session.scalars(stmt)
            query_results = scalars.all()

        return [self._build_core_event(event) for event in query_results]

    async def get_artist_events_amount(self, artist_id: UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(EventDB)
            .join(EventArtistDB, EventDB.id == EventArtistDB.event_id)
            .where(EventArtistDB.artist_id == artist_id)
        )
        async with self.sessionmaker.session() as session:
            result = await session.scalar(stmt)
        return result

    async def get_artist_names(self, ids: list[UUID]) -> dict[UUID, str]:
        stmt = select(ArtistDB).filter(ArtistDB.id.in_(ids))
        async with self.sessionmaker.session() as session:
            scalars = await session.scalars(stmt)
            query_results = scalars.all()
        result = {artist.id: artist.name for artist in query_results}
        return result

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
        return self._build_core_artist(db_artist=artist)

    async def unfollow(self, user_tg_id: int, artist_id: UUID) -> None:
        async with self.sessionmaker.session() as session:
            user = await self._user_by_tg_id(
                session=session, tg_id=user_tg_id, follows=False
            )
            if user is None:
                raise UserNotFound
            existing_follow = await session.get(
                FollowDB, {"user_id": user.id, "artist_id": artist_id}
            )
            if existing_follow is None:
                log.warning("Trying to remove unexisting follow, ignoring")
                return
            existing_follow.active = False
            session.add(existing_follow)
            await session.commit()

    async def add_follow(self, user_tg_id: int, artist_id: UUID) -> None:
        async with self.sessionmaker.session() as session:
            user = await self._user_by_tg_id(
                session=session, tg_id=user_tg_id, follows=False
            )
            if user is None:
                raise UserNotFound
            existing_follow = await session.get(
                FollowDB, {"user_id": user.id, "artist_id": artist_id}
            )
            if existing_follow is not None:
                if existing_follow.active is False:
                    existing_follow.active = True
                    session.add(existing_follow)
                    await session.commit()
                    return
                log.warning(
                    "Not adding a follow since it already exists and active. User "
                    "shouldn't be able to trigger this event"
                )
                return
            artist = await self._artist_by_uuid(
                session=session,
                artist_id=artist_id,
                genres=False,
                follows=False,
                socials=False,
            )
            if artist is None:
                raise ArtistNotFound
            follow = FollowDB(user=user, artist=artist, range_=Range.WORLDWIDE)
            session.add(follow)
            await session.commit()

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

    async def get_artist(self, id: UUID) -> Artist | None:
        async with self.sessionmaker.session() as session:
            artist = await self._get_artist(id, session)
        return artist

    async def add_user(self, user: RawUser) -> User:
        async with self.sessionmaker.session() as session:
            user_db = self._raw_to_db_user(user)
            session.add(user_db)
            try:
                await session.flush()
            except IntegrityError:
                raise UserAlreadyExists()
            await user_db.awaitable_attrs.follows
            await session.commit()
            result = self._db_to_core_user(user_db)
        return result

    async def get_user(self, tg_id: int) -> User | None:
        stmt = (
            select(UserDB)
            .where(UserDB.tg_id == tg_id)
            .options(selectinload(UserDB.follows))
            .options(selectinload(UserDB.settings))
        )
        async with self.sessionmaker.session() as session:
            scalars: ScalarResult = await session.scalars(stmt)

            user_db = scalars.first()
            if user_db is None:
                log.debug("Getting users, got zero results")
                return None
            log.debug("Getting users, got at least one result")
            return self._db_to_core_user(user_db)
