from uuid import UUID

from sqlalchemy import select

from band_tracker.core.artist import Artist, ArtistSocials
from band_tracker.core.artist_update import ArtistUpdate, ArtistUpdateSocials
from band_tracker.core.enums import EventSource
from band_tracker.core.event_update import EventUpdate
from band_tracker.db.models import (
    ArtistDB,
    ArtistImageDB,
    ArtistSocialsDB,
    ArtistTMDataDB,
    EventDB,
    EventTMDataDB,
)
from band_tracker.db.session import AsyncSessionmaker


class DAL:
    def __init__(self, sessionmaker: AsyncSessionmaker) -> None:
        self.sessionmaker = sessionmaker

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
        )
        return artist

    def _buld_db_socials(
        self, artist_id: UUID, socials: ArtistUpdateSocials
    ) -> ArtistSocialsDB:
        socials_db = ArtistSocialsDB(
            spotify=str(socials.spotify) if socials.spotify else None,
            youtube=str(socials.youtube) if socials.youtube else None,
            instagram=str(socials.instagram) if socials.instagram else None,
            artist_id=artist_id,
        )
        return socials_db

    async def add_artist(self, artist: ArtistUpdate) -> UUID:
        artist_tm_data = artist.get_source_specific_data(
            source=EventSource.ticketmaster_api
        )
        artist_db = ArtistDB(
            name=artist.name,
            tickets_link=str(artist.tickets_link),
        )
        async with self.sessionmaker.session() as session:
            session.add(artist_db)
            await session.flush()
            uuid = artist_db.id
            socials_db = self._buld_db_socials(artist_id=uuid, socials=artist.socials)
            tm_data_db = ArtistTMDataDB(id=artist_tm_data["id"], artist_id=uuid)
            images = [
                ArtistImageDB(url=image_url, artist_id=uuid)
                for image_url in artist.images
            ]
            session.add(tm_data_db)
            session.add_all(images)
            session.add(socials_db)
            await session.commit()
        return uuid

    async def get_artist_by_tm_id(self, tm_id: str) -> Artist | None:
        stmt = select(ArtistDB).join(ArtistTMDataDB).where(ArtistTMDataDB.id == tm_id)
        async with self.sessionmaker.session() as session:
            scalars = await session.scalars(stmt)
            artist_db = scalars.first()
            if artist_db is None:
                return None
            socials_db_result = await artist_db.awaitable_attrs.socials
            socials_db = socials_db_result[0]

        artist = self._build_core_artist(db_artist=artist_db, db_socials=socials_db)
        return artist

    async def get_artist_by_id(self, id: UUID) -> Artist | None:
        stmt = select(ArtistDB).where(ArtistDB.id == id)
        async with self.sessionmaker.session() as session:
            scalars = await session.scalars(stmt)
            artist_db = scalars.first()
            if artist_db is None:
                return None
            socials_db_result = await artist_db.awaitable_attrs.socials
            socials_db = socials_db_result[0]

        artist = self._build_core_artist(db_artist=artist_db, db_socials=socials_db)
        return artist

    async def update_artist_by_tm_id(self, artist: ArtistUpdate) -> UUID:
        tm_id = artist.source_specific_data[EventSource.ticketmaster_api]["id"]
        if await self.get_artist_by_tm_id(tm_id) is None:
            artist_id = await self.add_artist(artist)
            return artist_id

        stmt = select(ArtistDB).join(ArtistTMDataDB).where(ArtistTMDataDB.id == tm_id)
        async with self.sessionmaker.session() as session:
            scalars = await session.scalars(stmt)
            artist_db = scalars.first()

            artist_db.name = artist.name
            artist_db.tickets_link = str(artist.tickets_link)
            socials = artist_db.socials
            socials.instagram = (
                artist.socials.instagram if artist.socials.instagram else None
            )
            socials.youtube = artist.socials.youtube if artist.socials.youtube else None
            socials.spotify = artist.socials.spotify if artist.socials.spotify else None
            await session.flush()
            return artist_db.id

    async def add_event(self, event: EventUpdate) -> UUID:
        event_tm_data = event.get_source_specific_data(
            source=EventSource.ticketmaster_api
        )
        event_db = EventDB(
            title=event.title,
            venue=event.venue,
            venue_city=event.venue_city,
            venue_country=event.venue_country,
            start_date=event.date,
            ticket_url=event.ticket_url,
        )
        async with self.sessionmaker.session() as session:
            session.add(event_db)
            await session.flush()
            uuid = event_db.id
            tm_data_db = EventTMDataDB(id=event_tm_data["id"], event_id=uuid)
            session.add(tm_data_db)
            await session.commit()
        return uuid
