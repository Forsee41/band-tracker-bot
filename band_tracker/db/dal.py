from uuid import UUID

from pydantic import HttpUrl
from sqlalchemy import select

from band_tracker.core.artist import Artist
from band_tracker.core.enums import EventSource
from band_tracker.db.models import ArtistDB, ArtistImageDB, ArtistTMDataDB
from band_tracker.db.session import AsyncSessionmaker


class DAL:
    def __init__(self, sessionmaker: AsyncSessionmaker) -> None:
        self.sessionmaker = sessionmaker

    def _build_core_artist(self, db_artist: ArtistDB, tm_id: str) -> Artist:
        source_specific_data = {EventSource.ticketmaster_api: {"id": {tm_id}}}
        artist = Artist(
            id=db_artist.id,
            name=db_artist.name,
            spotify_link=HttpUrl(db_artist.spotify),
            tickets_link=HttpUrl(db_artist.tickets_link),
            inst_link=HttpUrl(db_artist.inst_link),
            youtube_link=HttpUrl(db_artist.youtube_link),
            source_specific_data=source_specific_data,
        )
        return artist

    async def add_artist(self, artist: Artist) -> UUID:
        artist_tm_data = artist.get_source_specific_data(
            source=EventSource.ticketmaster_api
        )
        artist_db = ArtistDB(
            name=artist.name,
            spotify=str(artist.spotify_link),
            tickets_link=str(artist.tickets_link),
            inst_link=str(artist.inst_link),
            youtube_link=str(artist.youtube_link),
        )
        async with self.sessionmaker.session() as session:
            session.add(artist_db)
            await session.flush()
            uuid = artist_db.id
            tm_data_db = ArtistTMDataDB(id=artist_tm_data["id"], artist_id=uuid)
            images = [
                ArtistImageDB(url=image_url, artist_id=uuid)
                for image_url in artist.images
            ]
            session.add(tm_data_db)
            session.add_all(images)
            await session.commit()
        return uuid

    async def get_artist_by_tm_id(self, tm_id: str) -> Artist | None:
        stmt = select(ArtistDB).join(ArtistTMDataDB).where(ArtistTMDataDB.id == tm_id)
        async with self.sessionmaker.session() as session:
            scalars = await session.scalars(stmt)
            artist_db = scalars.first()
        if artist_db is None:
            return None

        artist = self._build_core_artist(db_artist=artist_db, tm_id=tm_id)
        return artist

    async def get_artist_by_id(self, id: UUID) -> Artist | None:
        stmt = select(ArtistDB).where(ArtistDB.id == id)
        async with self.sessionmaker.session() as session:
            scalars = await session.scalars(stmt)
            artist_db = scalars.first()
            if artist_db is None:
                return None
            tm_id = artist_db.tm_data.id

        artist = self._build_core_artist(db_artist=artist_db, tm_id=tm_id)
        return artist

    async def update_artist_by_tm_id(self, artist: Artist) -> UUID:
        tm_id = artist.source_specific_data[EventSource.ticketmaster_api]["id"]
        if await self.get_artist_by_tm_id(tm_id) is None:
            artist_id = await self.add_artist(artist)
            return artist_id

        stmt = select(ArtistDB).join(ArtistTMDataDB).where(ArtistTMDataDB.id == tm_id)
        async with self.sessionmaker.session() as session:
            scalars = await session.scalars(stmt)
            artist_db = scalars.first()

            artist_db.name = artist.name
            artist_db.spotify = str(artist.spotify_link)
            artist_db.tickets_link = str(artist.tickets_link)
            artist_db.inst_link = str(artist.inst_link)
            artist_db.youtube_link = str(artist.youtube_link)
            await session.flush()
            return artist_db.id
