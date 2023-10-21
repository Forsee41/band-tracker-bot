import logging
import re
from datetime import datetime
from uuid import UUID

from sqlalchemy import desc, func, literal, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from band_tracker.core.artist import Artist, ArtistSocials
from band_tracker.core.enums import AdminNotificationLevel, EventSource
from band_tracker.core.event import Event, EventSales
from band_tracker.db.artist_update import ArtistUpdate, ArtistUpdateSocials
from band_tracker.db.errors import DALError
from band_tracker.db.event_update import EventUpdate, EventUpdateSales
from band_tracker.db.models import (
    AdminDB,
    ArtistAliasDB,
    ArtistDB,
    ArtistSocialsDB,
    ArtistTMDataDB,
    EventArtistDB,
    EventDB,
    EventTMDataDB,
    SalesDB,
)
from band_tracker.db.session import AsyncSessionmaker

log = logging.getLogger(__name__)


class BaseDAL:
    def __init__(self, sessionmaker: AsyncSessionmaker) -> None:
        self.sessionmaker = sessionmaker

    def _build_core_event(
        self, db_event: EventDB, db_sales: SalesDB, artist_ids: list[UUID]
    ) -> Event:
        sales = EventSales(
            price_min=db_sales.price_min,
            sale_start=db_sales.sale_start,
            sale_end=db_sales.sale_end,
            price_max=db_sales.price_max,
            currency=db_sales.currency,
        )

        event = Event(
            id=db_event.id,
            artist_ids=artist_ids,
            sales=sales,
            title=db_event.title,
            date=db_event.start_date,
            venue=db_event.venue,
            venue_city=db_event.venue_city,
            venue_country=db_event.venue_country,
            ticket_url=db_event.ticket_url,
            image=db_event.image,
        )
        return event

    def _build_core_artist(
        self, db_artist: ArtistDB, db_socials: ArtistSocialsDB
    ) -> Artist:
        socials = ArtistSocials(
            spotify=db_socials.spotify,
            instagram=db_socials.instagram,
            youtube=db_socials.youtube,
        )

        artist = Artist(
            id=db_artist.id,
            name=db_artist.name,
            tickets_link=db_artist.tickets_link,
            socials=socials,
            image=db_artist.image,
        )
        return artist


class PredictorDAL:
    def __init__(self, sessionmaker: AsyncSessionmaker) -> None:
        self.sessionmaker = sessionmaker

    async def get_event_amounts(self) -> list[tuple[datetime, int]]:
        # Using raw sql for query optimization, query has no params
        stmt = text(
            """
        SELECT DATE_TRUNC('day', start_date) as dates, count(id)
        FROM event
        GROUP BY DATE_TRUNC('day', start_date)
        ORDER BY DATE_TRUNC('day', start_date)
        """
        )
        async with self.sessionmaker.session() as session:
            raw_result = await session.execute(stmt)
            data = raw_result.fetchall()
        result = data
        return result


class BotDAL(BaseDAL):
    async def search_artist(
        self, search_str: str, similarity_min: float = 0.3
    ) -> list[Artist]:
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
        )
        async with self.sessionmaker.session() as session:
            scalars = await session.scalars(stmt)
            artists = scalars.all()
            return [
                self._build_core_artist(db_artist=artist, db_socials=artist.socials)
                for artist in artists
            ]

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
        stmt = select(ArtistDB).where(ArtistDB.id == id)
        async with self.sessionmaker.session() as session:
            scalars = await session.scalars(stmt)
            artist_db = scalars.first()
            if artist_db is None:
                return None
            socials_db_result = await artist_db.awaitable_attrs.socials
            socials_db = socials_db_result

        artist = self._build_core_artist(db_artist=artist_db, db_socials=socials_db)
        return artist


class UpdateDAL(BaseDAL):
    def __init__(self, sessionmaker: AsyncSessionmaker) -> None:
        self.sessionmaker = sessionmaker

    async def update_artist(self, artist: ArtistUpdate) -> UUID:
        tm_id = artist.source_specific_data[EventSource.ticketmaster_api]["id"]
        if await self._get_artist_by_tm_id(tm_id) is None:
            log.debug(f"Artist with tm id {tm_id} is not present, adding a new one")
            artist_id = await self._add_artist(artist)
            return artist_id

        if artist.name not in artist.aliases:
            artist.aliases.append(artist.name)

        async with self.sessionmaker.session() as session:
            artist_db = await self._artist_by_tm_id(session=session, tm_id=tm_id)
            assert artist_db is not None
            artist_db.name = artist.name
            artist_db.tickets_link = str(artist.tickets_link)
            artist_db.image = str(artist.image)
            socials = await artist_db.awaitable_attrs.socials
            socials.instagram = (
                str(artist.socials.instagram) if artist.socials.instagram else None
            )
            socials.youtube = (
                str(artist.socials.youtube) if artist.socials.youtube else None
            )
            socials.spotify = (
                str(artist.socials.spotify) if artist.socials.spotify else None
            )
            await self._add_new_aliases(
                session=session, artist_id=artist_db.id, aliases=artist.aliases
            )
            session.add(socials)
            await session.commit()
            return artist_db.id

    async def update_event(self, event: EventUpdate) -> tuple[UUID, list[UUID]]:
        event_tm_data = event.get_source_specific_data(
            source=EventSource.ticketmaster_api
        )
        event_tm_id = event_tm_data["id"]
        if not await self._is_event_exists(event_tm_id):
            log.info(f"Event with tm id {event_tm_id} is not present, adding a new one")
            return await self._add_event(event)

        ticket_url = str(event.ticket_url) if event.ticket_url else None
        image = str(event.image) if event.image else None

        async with self.sessionmaker.session() as session:
            event_db = await self._event_by_tm_id(session=session, tm_id=event_tm_id)
            assert event_db is not None
            uuid = event_db.id

            event_db.venue = event.venue
            event_db.venue_city = event.venue_city
            event_db.venue_country = event.venue_country
            event_db.title = event.title
            event_db.ticket_url = ticket_url
            event_db.start_date = event.date
            event_db.image = image

            sales_result = await event_db.awaitable_attrs.sales
            sales = sales_result[0]
            sales.sale_end = event.sales.sale_end
            sales.sale_start = event.sales.sale_start
            sales.currency = event.sales.currency
            sales.price_max = event.sales.price_max
            sales.price_min = event.sales.price_min
            session.add(sales)
            await session.commit()

        try:
            artist_event_uuids = await self._link_event_to_artists(
                event_tm_id=event_tm_id,
                artist_tm_ids=event.artists,
            )
        except DALError:
            log.warning(
                f"Attempt to link unexciting event of tm_id {event_tm_id} to artists"
            )
            raise

        return uuid, artist_event_uuids

    async def _get_artist_by_tm_id(self, tm_id: str) -> Artist | None:
        async with self.sessionmaker.session() as session:
            artist_db = await self._artist_by_tm_id(session=session, tm_id=tm_id)
            if artist_db is None:
                return None
            socials_db = await artist_db.awaitable_attrs.socials

        artist = self._build_core_artist(db_artist=artist_db, db_socials=socials_db)
        return artist

    async def _get_event_by_tm_id(self, tm_id: str) -> Event | None:
        async with self.sessionmaker.session() as session:
            event_db = await self._event_by_tm_id(session=session, tm_id=tm_id)
            if event_db is None:
                return None
            sales_result = await event_db.awaitable_attrs.sales
            sales_db = sales_result[0]

            artists = await event_db.awaitable_attrs.artists
            artist_ids = [artist.id for artist in artists]

            event = self._build_core_event(event_db, sales_db, artist_ids)
            return event

    async def _artist_by_tm_id(
        self, session: AsyncSession, tm_id: str
    ) -> ArtistDB | None:
        artist_query = (
            select(ArtistDB).join(ArtistTMDataDB).where(ArtistTMDataDB.id == tm_id)
        )
        scalar = await session.scalars(artist_query)
        artist_db = scalar.first()
        return artist_db

    async def _event_by_tm_id(
        self, session: AsyncSession, tm_id: str
    ) -> EventDB | None:
        stmt = select(EventDB).join(EventTMDataDB).where(EventTMDataDB.id == tm_id)
        scalar = await session.scalars(stmt)
        event_db = scalar.first()
        return event_db

    def _build_db_socials(
        self, artist_id: UUID, socials: ArtistUpdateSocials
    ) -> ArtistSocialsDB:
        socials_db = ArtistSocialsDB(
            spotify=str(socials.spotify) if socials.spotify else None,
            youtube=str(socials.youtube) if socials.youtube else None,
            instagram=str(socials.instagram) if socials.instagram else None,
            artist_id=artist_id,
        )
        return socials_db

    def _build_db_artist_aliases(
        self, artist_id: UUID, aliases: list[str]
    ) -> list[ArtistAliasDB]:
        return [ArtistAliasDB(artist_id=artist_id, alias=alias) for alias in aliases]

    async def _add_new_aliases(
        self, session: AsyncSession, artist_id: UUID, aliases: list[str]
    ) -> None:
        stmt = select(ArtistAliasDB.alias).filter(ArtistAliasDB.alias.in_(aliases))
        existing_aliases_tuples = await session.execute(stmt)
        existing_aliases = [alias[0] for alias in existing_aliases_tuples.all()]
        new_aliases = [alias for alias in aliases if alias not in existing_aliases]
        db_aliases = self._build_db_artist_aliases(
            artist_id=artist_id, aliases=new_aliases
        )
        session.add_all(db_aliases)

    async def _add_artist(self, artist: ArtistUpdate) -> UUID:
        if artist.name not in artist.aliases:
            artist.aliases.append(artist.name)
        artist_tm_data = artist.get_source_specific_data(
            source=EventSource.ticketmaster_api
        )
        artist_db = ArtistDB(
            name=artist.name,
            tickets_link=str(artist.tickets_link),
            image=str(artist.image),
        )
        async with self.sessionmaker.session() as session:
            session.add(artist_db)
            await session.flush()
            uuid = artist_db.id
            socials_db = self._build_db_socials(artist_id=uuid, socials=artist.socials)
            tm_data_db = ArtistTMDataDB(id=artist_tm_data["id"], artist_id=uuid)
            await self._add_new_aliases(
                session=session, artist_id=uuid, aliases=artist.aliases
            )

            session.add(tm_data_db)
            session.add(socials_db)
            await session.commit()
        return uuid

    async def _link_event_to_artists(
        self,
        event_tm_id: str,
        artist_tm_ids: list[str],
    ) -> list[UUID]:
        """
        Links event to its artists by tm ids. Ignores non existing artists.
        Returns a list of newly linked EventArtist UUID's.
        Raises DALError if event tm id is not present in db.
        """
        async with self.sessionmaker.session() as session:
            event_db = await self._event_by_tm_id(session=session, tm_id=event_tm_id)
            if event_db is None:
                raise DALError(f"event with tm id {event_tm_id} is not present in db")
            already_linked_artists = await event_db.awaitable_attrs.artists
            already_linked_ids = [artist.id for artist in already_linked_artists]
            new_artists: list[UUID] = []

            for artist_tm_id in artist_tm_ids:
                artist_db = await self._artist_by_tm_id(
                    session=session, tm_id=artist_tm_id
                )
                if artist_db is None:
                    continue
                if artist_db.id not in already_linked_ids:
                    event_db.artists.append(artist_db)
                    new_artists.append(artist_db.id)

            session.add(event_db)
            await session.commit()

        event_artist_uuids = await self._get_event_artists_by_uuids(
            artist_uuids=new_artists, event_uuid=event_db.id
        )

        return event_artist_uuids

    async def _get_event_artists_by_uuids(
        self, artist_uuids: list[UUID], event_uuid: UUID
    ) -> list[UUID]:
        stmt = (
            select(EventArtistDB.id)
            .join(ArtistDB)
            .join(EventDB)
            .where(EventDB.id == event_uuid, ArtistDB.id.in_(artist_uuids))
        )
        async with self.sessionmaker.session() as session:
            ids = await session.scalars(stmt)
        return ids.all()

    async def _is_event_exists(self, event_tm_id: str) -> bool:
        async with self.sessionmaker.session() as session:
            event_db = await self._event_by_tm_id(session=session, tm_id=event_tm_id)
        return bool(event_db)

    def _buld_event_sales(self, event_id: UUID, sales: EventUpdateSales) -> SalesDB:
        sales_db = SalesDB(
            sale_start=sales.sale_start,
            sale_end=sales.sale_end,
            price_max=sales.price_max,
            price_min=sales.price_min,
            currency=sales.currency,
            event_id=event_id,
        )

        return sales_db

    async def _add_event(self, event: EventUpdate) -> tuple[UUID, list[UUID]]:
        event_tm_data = event.get_source_specific_data(
            source=EventSource.ticketmaster_api
        )
        event_tm_id = event_tm_data["id"]

        ticket_url = str(event.ticket_url) if event.ticket_url else None
        image = str(event.image) if event.image else None

        event_db = EventDB(
            title=event.title,
            venue=event.venue,
            venue_city=event.venue_city,
            venue_country=event.venue_country,
            start_date=event.date,
            ticket_url=ticket_url,
            image=image,
        )
        async with self.sessionmaker.session() as session:
            session.add(event_db)
            await session.flush()
            uuid = event_db.id
            sales = self._buld_event_sales(uuid, event.sales)
            tm_data_db = EventTMDataDB(id=event_tm_id, event_id=uuid)

            session.add(tm_data_db)
            session.add(sales)
            await session.commit()
        try:
            event_artist_uuids = await self._link_event_to_artists(
                event_tm_id=event_tm_id,
                artist_tm_ids=event.artists,
            )
        except DALError:
            log.warning(
                f"Attempt to link unexciting event of tm_id {event_tm_id} to artists"
            )
            raise

        return uuid, event_artist_uuids
