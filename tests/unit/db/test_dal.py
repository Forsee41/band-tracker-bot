import pytest
from pydantic import HttpUrl
from sqlalchemy import select

from band_tracker.core.artist import Artist
from band_tracker.core.enums import EventSource
from band_tracker.db.dal import DAL
from band_tracker.db.models import ArtistDB


class TestDAL:
    async def test_add_artist(self, dal: DAL) -> None:
        artist = Artist(
            name="name",
            spotify_link=HttpUrl("https://spotify.com"),
            tickets_link=HttpUrl("https://tickets_url.com"),
            inst_link=HttpUrl("https://inst.com"),
            youtube_link=HttpUrl("https://youtube.com"),
            upcoming_events_amount=13,
            source_specific_data={
                EventSource.ticketmaster_api: {"id": "ticketmaster_id"}
            },
        )
        artist_id = await dal.add_artist(artist)

        stmt = select(ArtistDB).where(ArtistDB.id == artist_id)
        async with dal.sessionmaker.session() as session:
            selected_artist = await session.scalars(stmt)
            selected_artist = selected_artist.first()

        assert selected_artist.name == "name"
        assert selected_artist.spotify == "https://spotify.com/"
        assert selected_artist.tickets_link == "https://tickets_url.com/"
        assert selected_artist.inst_link == "https://inst.com/"
        assert selected_artist.youtube_link == "https://youtube.com/"


if __name__ == "__main__":
    pytest.main()
