import logging
from uuid import UUID

from sqlalchemy import select

from band_tracker.core.artist import Artist, ArtistSocials
from band_tracker.core.artist_update import ArtistUpdate, ArtistUpdateSocials
from band_tracker.core.enums import EventSource
from band_tracker.core.errors import DALError
from band_tracker.core.event_update import EventUpdate
from band_tracker.db.models import (
    ArtistDB,
    ArtistImageDB,
    ArtistSocialsDB,
    ArtistTMDataDB,
    EventDB,
    EventImageDB,
    EventTMDataDB,
)
from band_tracker.db.session import AsyncSessionmaker

log = logging.getLogger(__name__)


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

    async def _link_event_to_artists(
        self,
        event_tm_id: str,
        artist_tm_ids: list[str],
        return_skipped: bool = False,
        remove_links: bool = True,
    ) -> list[str]:
        """
        Links event to its artists by tm ids. Ignores non existing artists.
        Returns a list of tm ids of linked artists if return_skipped is False
        or a list of skipped ids if return_skipped is True.
        Raises DALError if event tm id is not present in db.
        Removes existing links if ids are not present in artist_tm_ids
        """
        stmt = (
            select(EventDB).join(EventTMDataDB).where(EventTMDataDB.id == event_tm_id)
        )
        linked_artist_tm_ids = []
        artist_db_ids = []
        async with self.sessionmaker.session() as session:
            scalars = await session.scalars(stmt)
            event_db = scalars.first()
            if event_db is None:
                raise DALError(f"event with tm id {event_tm_id} is not present in db")
            already_linked_artists = await event_db.awaitable_attrs.artists
            already_linked_ids = [artist.id for artist in already_linked_artists]

            for artist_tm_id in artist_tm_ids:
                stmt = (
                    select(ArtistDB)
                    .join(ArtistTMDataDB)
                    .where(ArtistTMDataDB.id == artist_tm_id)
                )
                scalar = await session.scalars(stmt)
                artist_db = scalar.first()
                if artist_db is None:
                    continue
                if artist_db.id not in already_linked_ids:
                    event_db.artists.append(artist_db)
                artist_db_ids.append(artist_db.id)
                linked_artist_tm_ids.append(artist_tm_id)

            if remove_links:
                await event_db.awaitable_attrs.artists
                for already_linked_artist in already_linked_artists:
                    if already_linked_artist.id not in artist_db_ids:
                        event_db.artists.remove(already_linked_artist)
            session.add(event_db)
            session.commit()
        if return_skipped:
            return [
                artist_tm_id
                for artist_tm_id in artist_tm_ids
                if artist_tm_id not in linked_artist_tm_ids
            ]
        return linked_artist_tm_ids

    async def _is_event_exists(self, event_tm_id: str) -> bool:
        stmt = (
            select(EventDB).join(EventTMDataDB).where(EventTMDataDB.id == event_tm_id)
        )
        async with self.sessionmaker.session() as session:
            scalars = await session.scalars(stmt)
            event_db = scalars.first()
        return bool(event_db)

    async def update_event(self, event: EventUpdate) -> UUID:
        event_tm_data = event.get_source_specific_data(
            source=EventSource.ticketmaster_api
        )
        event_tm_id = event_tm_data["id"]
        if await self._is_event_exists(event_tm_id):
            return await self.add_event(event)

        stmt = (
            select(EventDB).join(EventTMDataDB).where(EventTMDataDB.id == event_tm_id)
        )
        async with self.sessionmaker.session() as session:
            scalars = await session.scalars(stmt)
            event_db = scalars.first()
            uuid = event_db.id
            # TODO: update images here

        await self._link_event_to_artists(
            event_tm_id=event_tm_id, artist_tm_ids=event.artists
        )
        return uuid

    async def add_event(self, event: EventUpdate) -> UUID:
        event_tm_data = event.get_source_specific_data(
            source=EventSource.ticketmaster_api
        )
        event_tm_id = event_tm_data["id"]
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
            tm_data_db = EventTMDataDB(id=event_tm_id, event_id=uuid)
            images = [
                EventImageDB(url=image_url, event_id=uuid) for image_url in event.images
            ]
            session.add_all(images)
            session.add(tm_data_db)
            await session.commit()
        try:
            await self._link_event_to_artists(
                event_tm_id=event_tm_id, artist_tm_ids=event.artists
            )
        except DALError:
            log.warning(
                f"Attempt to link unexsitning event of tm_id {event_tm_id} to artists"
            )
        return uuid
