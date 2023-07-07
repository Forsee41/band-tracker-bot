import pytest

from band_tracker.core.artist import Artist
from band_tracker.core.enums import EventSource
from band_tracker.db.dal import DAL


class TestDAL:
    async def test_add_artist(self, dal: DAL) -> None:
        artist = Artist(
            id="",
            name="name",
            spotify_link="https://spotify.com",
            tickets_link="https://tickets_url.com",
            inst_link="https://inst.com",
            youtube_link="https://youtube.com",
            upcoming_events_amount=0,
            _source_specific_data={
                EventSource.ticketmaster_api: {"id": "ticketmaster_id"}
            },
        )
        await dal.add_artist(artist)


if __name__ == "__main__":
    pytest.main()
