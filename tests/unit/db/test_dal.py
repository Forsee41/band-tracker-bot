import pytest
from pydantic import HttpUrl

from band_tracker.core.artist import Artist
from band_tracker.core.enums import EventSource
from band_tracker.db.dal import DAL


class TestDAL:
    async def test_add_artist(self, dal: DAL) -> None:
        artist = Artist(
            name="name",
            socials={
                "spotify": HttpUrl(
                    "https://open.spotify.com/artist"
                    "/5HAtRoEPUvGSA7ziTGB1cF?autoplay=true"
                ),
                "instagram": HttpUrl("http://www.instagram.com/theorblive"),
                "youtube": HttpUrl(
                    "https://www.youtube.com/channel/UCpoyFBLTLfbT2Z1D1AnlvLg"
                ),
            },
            tickets_link=HttpUrl("https://tickets_url.com"),
            source_specific_data={
                EventSource.ticketmaster_api: {"id": "ticketmaster_id"}
            },
            images=[],
        )
        await dal.add_artist(artist)


if __name__ == "__main__":
    pytest.main()
