import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from band_tracker.core.artist import Artist, ArtistSocials
from band_tracker.core.event import Event, EventSales
from band_tracker.core.follow import Follow
from band_tracker.core.user import RawUser, User
from band_tracker.core.user_settings import UserSettings
from band_tracker.db.models import ArtistDB, EventDB, FollowDB, UserDB, UserSettingsDB
from band_tracker.db.session import AsyncSessionmaker

log = logging.getLogger(__name__)


class BaseDAL:
    def __init__(self, sessionmaker: AsyncSessionmaker) -> None:
        self.sessionmaker = sessionmaker

    async def _artist_by_uuid(
        self,
        session: AsyncSession,
        artist_id: UUID,
        follows: bool = True,
        genres: bool = True,
        socials: bool = True,
    ) -> ArtistDB | None:
        stmt = select(ArtistDB).where(ArtistDB.id == artist_id)
        if follows:
            stmt = stmt.options(selectinload(ArtistDB.follows))
        if genres:
            stmt = stmt.options(selectinload(ArtistDB.genres))
        if socials:
            stmt = stmt.options(selectinload(ArtistDB.socials))
        scalars = await session.scalars(stmt)
        artist = scalars.first()
        return artist

    async def _get_artist(self, id: UUID, session: AsyncSession) -> Artist | None:
        stmt = (
            select(ArtistDB)
            .where(ArtistDB.id == id)
            .options(selectinload(ArtistDB.genres))
            .options(selectinload(ArtistDB.socials))
        )
        scalars = await session.scalars(stmt)
        artist_db = scalars.first()
        if artist_db is None:
            return None

        artist = self._build_core_artist(db_artist=artist_db)
        return artist

    async def get_user_by_uuid(self, id: UUID) -> User | None:
        stmt = select(UserDB).where(UserDB.id == id)
        async with self.sessionmaker.session() as session:
            scalars = await session.scalars(stmt)
            user_db = scalars.first()
            if user_db is None:
                return None

            user = self._db_to_core_user(user_db)
            return user

    async def get_event(self, id: UUID) -> Event | None:
        stmt = (
            select(EventDB)
            .where(EventDB.id == id)
            .options(selectinload(EventDB.sales))
            .options(selectinload(EventDB.artists))
        )
        async with self.sessionmaker.session() as session:
            scalars = await session.scalars(stmt)
            event_db = scalars.first()
            if event_db is None:
                return None

            event = self._build_core_event(event_db)
            return event

    async def _user_by_tg_id(
        self,
        session: AsyncSession,
        tg_id: int,
        follows: bool = True,
    ) -> UserDB | None:
        stmt = select(UserDB).where(UserDB.tg_id == tg_id)
        if follows:
            stmt = stmt.options(selectinload(UserDB.follows))
        scalars = await session.scalars(stmt)
        user = scalars.first()
        return user

    def _build_core_event(self, db_event: EventDB) -> Event:
        db_sales = db_event.sales[0]
        sales = EventSales(
            price_min=db_sales.price_min,
            sale_start=db_sales.sale_start,
            sale_end=db_sales.sale_end,
            price_max=db_sales.price_max,
            currency=db_sales.currency,
        )

        event = Event(
            id=db_event.id,
            artist_ids=[artist.id for artist in db_event.artists],
            sales=sales,
            title=db_event.title,
            date=db_event.start_date,
            venue=db_event.venue,
            venue_city=db_event.venue_city,
            venue_country=db_event.venue_country,
            ticket_url=db_event.ticket_url,
            image=db_event.image,
            thumbnail=db_event.thumbnail,
            last_update=db_event.last_update,
        )
        return event

    def _build_core_artist(self, db_artist: ArtistDB) -> Artist:
        db_socials = db_artist.socials
        socials = ArtistSocials(
            spotify=db_socials.spotify,
            instagram=db_socials.instagram,
            youtube=db_socials.youtube,
            wiki=db_socials.wiki,
        )
        genres = db_artist.genres
        genre_names = [genre.name for genre in genres]

        artist = Artist(
            id=db_artist.id,
            name=db_artist.name,
            tickets_link=db_artist.tickets_link,
            socials=socials,
            image=db_artist.image,
            thumbnail=db_artist.thumbnail,
            genres=genre_names,
            description=db_artist.description,
        )
        return artist

    def _raw_to_db_user(self, user: RawUser) -> UserDB:
        db_settings = self._core_to_db_user_settings(user.settings)
        db_user = UserDB(
            tg_id=user.tg_id,
            name=user.name,
            join_date=user.join_date,
            settings=db_settings,
        )
        return db_user

    def _db_to_core_user(self, user_db: UserDB) -> User:
        settings = self._db_to_core_user_settings(user_db.settings)
        follows = {
            follow_db.artist_id: self._db_to_core_follow(follow_db)
            for follow_db in user_db.follows
            if follow_db.active
        }
        user = User(
            id=user_db.id,
            tg_id=user_db.tg_id,
            name=user_db.name,
            join_date=user_db.join_date,
            settings=settings,
            follows=follows,
        )
        return user

    def _db_to_core_follow(self, follow_db: FollowDB) -> Follow:
        return Follow(
            artist=follow_db.artist_id,
            range_=follow_db.range_,
            notify=follow_db.notify,
        )

    def _core_to_db_user_settings(self, settings: UserSettings) -> UserSettingsDB:
        assert settings
        settings_db = UserSettingsDB(is_muted=False)
        return settings_db

    def _db_to_core_user_settings(self, settings_db: UserSettingsDB) -> UserSettings:
        assert settings_db
        settings = UserSettings.default()
        return settings
