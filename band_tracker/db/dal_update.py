import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from band_tracker.core.artist import Artist
from band_tracker.core.enums import EventSource
from band_tracker.core.event import Event
from band_tracker.db.artist_update import ArtistUpdate, ArtistUpdateSocials
from band_tracker.db.dal_base import BaseDAL
from band_tracker.db.errors import DALError
from band_tracker.db.event_update import EventUpdate, EventUpdateSales
from band_tracker.db.models import (
    ArtistAliasDB,
    ArtistDB,
    ArtistGenreDB,
    ArtistNameDB,
    ArtistSocialsDB,
    ArtistTMDataDB,
    EventArtistDB,
    EventDB,
    EventTMDataDB,
    GenreDB,
    SalesDB,
)
from band_tracker.db.session import AsyncSessionmaker

log = logging.getLogger(__name__)


class UpdateDAL(BaseDAL):
    def __init__(self, sessionmaker: AsyncSessionmaker) -> None:
        self.sessionmaker = sessionmaker

    async def update_artists(self, artists: list[ArtistUpdate]) -> None:
        for artist in artists:
            await self.update_artist(artist)

    async def update_artist(self, artist: ArtistUpdate) -> UUID:
        tm_id = artist.source_specific_data[EventSource.ticketmaster_api]["id"]
        if await self.get_artist_by_tm_id(tm_id) is None:
            log.debug(f"Artist with tm id {tm_id} is not present, adding a new one")
            artist_id = await self._add_artist(artist)
            return artist_id

        if artist.name not in artist.aliases:
            artist.aliases.append(artist.name)

        async with self.sessionmaker.session() as session:
            artist_db = await self._artist_by_tm_id(session=session, tm_id=tm_id)

            assert artist_db is not None

            artist_db.name = artist.name
            artist_db.tickets_link = (
                str(artist.tickets_link) if artist.tickets_link else None
            )
            artist_db.image = str(artist.main_image) if artist.main_image else None
            artist_db.thumbnail = (
                str(artist.thumbnail_image) if artist.thumbnail_image else None
            )
            artist_db.description = artist.description

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
            socials.wiki = str(artist.socials.wiki) if artist.socials.wiki else None

            new_genres = await self._get_new_genres(
                session=session, artist_id=artist_db.id, genres=artist.genres
            )
            artist_db.genres.extend(new_genres)

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
        image = str(event.main_image) if event.main_image else None
        thumbnail = str(event.thumbnail_image) if event.thumbnail_image else None

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
            event_db.thumbnail = thumbnail
            event_db.last_update = datetime.strptime(
                datetime.now().strftime("%Y-%m-%d"), "%Y-%m-%d"
            )

            sales_result = await event_db.awaitable_attrs.sales
            sales = sales_result[0]
            sales.sale_end = event.sales.sale_end
            sales.sale_start = event.sales.sale_start
            sales.currency = event.sales.currency
            sales.price_max = event.sales.price_max
            sales.price_min = event.sales.price_min
            session.add(sales)
            await session.commit()

        await self.update_artists(event.artists)

        try:
            artist_ids = event.get_artist_ids()
            artist_event_uuids = await self._link_event_to_artists(
                event_tm_id=event_tm_id,
                artist_tm_ids=artist_ids,
            )
        except DALError:
            log.warning(
                f"Attempt to link unexciting event of tm_id {event_tm_id} to artists"
            )
            raise

        return uuid, artist_event_uuids

    async def get_artist_by_tm_id(self, tm_id: str) -> Artist | None:
        async with self.sessionmaker.session() as session:
            artist_db = await self._artist_by_tm_id(session=session, tm_id=tm_id)
            if artist_db is None:
                return None

        artist = self._build_core_artist(db_artist=artist_db)
        return artist

    async def _get_event_by_tm_id(self, tm_id: str) -> Event | None:
        async with self.sessionmaker.session() as session:
            event_db = await self._event_by_tm_id(session=session, tm_id=tm_id)
            if event_db is None:
                return None

            event = self._build_core_event(event_db)
            return event

    async def _artist_by_tm_id(
        self, session: AsyncSession, tm_id: str
    ) -> ArtistDB | None:
        artist_query = (
            select(ArtistDB)
            .join(ArtistTMDataDB)
            .where(ArtistTMDataDB.id == tm_id)
            .options(joinedload(ArtistDB.genres))
            .options(selectinload(ArtistDB.socials))
        )
        scalar = await session.scalars(artist_query)
        artist_db = scalar.first()
        return artist_db

    async def _event_by_tm_id(
        self, session: AsyncSession, tm_id: str
    ) -> EventDB | None:
        stmt = (
            select(EventDB)
            .join(EventTMDataDB)
            .where(EventTMDataDB.id == tm_id)
            .options(selectinload(EventDB.sales))
            .options(selectinload(EventDB.artists))
        )
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
            wiki=str(socials.wiki) if socials.wiki else None,
            artist_id=artist_id,
        )
        return socials_db

    async def _get_new_genres(
        self, session: AsyncSession, artist_id: UUID, genres: list[str]
    ) -> list[GenreDB]:
        artist_genre_names = (
            select(GenreDB.name)
            .join(ArtistGenreDB, GenreDB.id == ArtistGenreDB.genre_id)
            .filter(ArtistGenreDB.artist_id == artist_id)
        )
        execution_result = await session.execute(artist_genre_names)
        current_genre_names = [name[0] for name in execution_result]

        new_genre_names = [
            genre for genre in genres if genre not in current_genre_names
        ]
        new_db_genres = await self._get_db_genres(session, new_genre_names)

        return new_db_genres

    async def _get_db_genres(
        self, session: AsyncSession, genres: list[str]
    ) -> list[GenreDB]:
        genres_query = select(GenreDB).filter(GenreDB.name.in_(genres))
        existing_genres = (await session.execute(genres_query)).fetchall()

        existing_genres_names = {genre[0].name: genre[0] for genre in existing_genres}

        result = []
        for genre in genres:
            genre_db = existing_genres_names.get(genre)

            if not genre_db:
                genre_db = GenreDB(name=genre)
                session.add(genre_db)
            result.append(genre_db)
        await session.commit()

        return result

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
        tickets_link = str(artist.tickets_link) if artist.tickets_link else None
        image = str(artist.main_image) if artist.main_image else None
        thumbnail = str(artist.thumbnail_image) if artist.thumbnail_image else None
        description = artist.description

        artist_db = ArtistDB(
            name=artist.name,
            tickets_link=tickets_link,
            image=image,
            thumbnail=thumbnail,
            description=description,
        )
        async with self.sessionmaker.session() as session:
            db_genres = await self._get_db_genres(session, artist.genres)
            log.debug("GENRES: " + str(db_genres))
            artist_db.genres.extend(db_genres)
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
        image = str(event.main_image) if event.main_image else None
        thumbnail = str(event.thumbnail_image) if event.thumbnail_image else None

        event_db = EventDB(
            title=event.title,
            venue=event.venue,
            venue_city=event.venue_city,
            venue_country=event.venue_country,
            start_date=event.date,
            ticket_url=ticket_url,
            image=image,
            thumbnail=thumbnail,
            last_update=datetime.strptime(
                datetime.now().strftime("%Y-%m-%d"), "%Y-%m-%d"
            ),
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

        await self.update_artists(event.artists)
        try:
            artist_ids = event.get_artist_ids()
            event_artist_uuids = await self._link_event_to_artists(
                event_tm_id=event_tm_id,
                artist_tm_ids=artist_ids,
            )
        except DALError:
            log.warning(
                f"Attempt to link unexciting event of tm_id {event_tm_id} to artists"
            )
            raise

        return uuid, event_artist_uuids

    async def get_external_artist_names(self) -> list[str]:
        async with self.sessionmaker.session() as session:
            query = select(ArtistNameDB.name)
            result = await session.execute(query)
            artist_names = [row[0] for row in result.fetchall()]

        return artist_names

    async def add_external_artist_name(self, name: str) -> None:
        artist_name = ArtistNameDB(name=name)

        async with self.sessionmaker.session() as session:
            session.add(artist_name)
            await session.flush()
            await session.commit()
        log.info(name.join(" was added."))

    async def get_tm_ids(self) -> list[str]:
        async with self.sessionmaker.session() as session:
            query = select(ArtistTMDataDB.id)
            result = await session.execute(query)
            artist_ids = [row[0] for row in result.fetchall()]

        return artist_ids
