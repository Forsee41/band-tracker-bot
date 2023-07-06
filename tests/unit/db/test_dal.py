import pytest

from band_tracker.core.artist import Artist
from band_tracker.core.enums import EventSource
from band_tracker.db.dal import DAL


class TestDAL:
    async def test_add_artist(self, dal: DAL) -> None:
        artist = Artist(
            id="",
            name="name",
            shortname="shortname",
            spotify_link="spotify",
            tickets_link="tickets_url",
            upcoming_events_amount=0,
            score=0,
            images=["url1", "url2"],
            genres=[],
            _source_specific_data={EventSource.ticketmaster: {"id": "ticketmaster_id"}},
        )
        await dal.add_artist(artist)


if __name__ == "__main__":
    pytest.main()
