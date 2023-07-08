from uuid import UUID

from band_tracker.core.artist import Artist
from band_tracker.core.enums import EventSource
from band_tracker.db.models import ArtistDB, ArtistImageDB, ArtistTMDataDB
from band_tracker.db.session import AsyncSessionmaker


class DAL:
    def __init__(self, sessionmaker: AsyncSessionmaker) -> None:
        self.sessionmaker = sessionmaker

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
