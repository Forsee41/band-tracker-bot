from typing import Callable

import pytest
from pydantic import HttpUrl

from band_tracker.core.artist_update import ArtistUpdate
from band_tracker.core.enums import EventSource
from band_tracker.db.dal import DAL


class TestUpdateArtistDAL:
    async def test_artist_fields_being_updated(
        self, dal: DAL, get_artist_update: Callable[[], ArtistUpdate]
    ) -> None:
        artist = get_artist_update()
        tm_id = artist.source_specific_data[EventSource.ticketmaster_api]["id"]
        await dal.add_artist(artist)
        artist.name = "new_artist_name"
        await dal.update_artist_by_tm_id(artist)
        queried_artist = await dal.get_artist_by_tm_id(tm_id)
        assert queried_artist
        assert queried_artist.name == "new_artist_name"

    async def test_socials_being_updated(
        self, dal: DAL, get_artist_update: Callable[[], ArtistUpdate]
    ) -> None:
        artist = get_artist_update()
        tm_id = artist.source_specific_data[EventSource.ticketmaster_api]["id"]
        await dal.add_artist(artist)
        artist.socials.instagram = HttpUrl("https://new_artist_instagram.com/")
        artist.socials.spotify = HttpUrl("https://new_artist_spotify.com/")
        artist.socials.youtube = HttpUrl("https://new_artist_youtube.com/")
        await dal.update_artist_by_tm_id(artist)
        queried_artist = await dal.get_artist_by_tm_id(tm_id)
        assert queried_artist
        assert queried_artist.socials.instagram == "https://new_artist_instagram.com/"
        assert queried_artist.socials.spotify == "https://new_artist_spotify.com/"
        assert queried_artist.socials.youtube == "https://new_artist_youtube.com/"


if __name__ == "__main__":
    pytest.main()
