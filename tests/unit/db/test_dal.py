import pytest
from pydantic import HttpUrl

from band_tracker.core.artist_update import ArtistUpdate, ArtistUpdateSocials
from band_tracker.core.enums import EventSource
from band_tracker.db.dal import DAL


class TestDAL:
    default_artist = ArtistUpdate(
        name="name",
        socials=ArtistUpdateSocials(
            spotify=HttpUrl(
                "https://open.spotify.com/artist"
                "/5HAtRoEPUvGSA7ziTGB1cF?autoplay=true"
            ),
            instagram=HttpUrl("http://www.instagram.com/theorblive"),
            youtube=HttpUrl("https://www.youtube.com/channel/UCpoyFBLTLfbT2Z1D1AnlvLg"),
        ),
        tickets_link=HttpUrl("https://tickets_url.com"),
        source_specific_data={EventSource.ticketmaster_api: {"id": "ticketmaster_id"}},
        genres=[],
        aliases=[],
        images=None,
    )

    async def test_add_artist(self, dal: DAL) -> None:
        await dal.add_artist(self.default_artist)
        result_artist = await dal.get_artist_by_tm_id("ticketmaster_id")

        assert result_artist
        assert result_artist.name == "name"
        assert result_artist.tickets_link == "https://tickets_url.com/"


if __name__ == "__main__":
    pytest.main()
