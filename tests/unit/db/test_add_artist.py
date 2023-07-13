from typing import Callable

import pytest
from sqlalchemy.exc import IntegrityError

from band_tracker.core.artist_update import ArtistUpdate
from band_tracker.core.enums import EventSource
from band_tracker.db.dal import DAL


class TestAddArtistDAL:
    async def test_add_artist(
        self, dal: DAL, get_artist_update: Callable[[str], ArtistUpdate]
    ) -> None:
        artist = get_artist_update("gosha")
        await dal.add_artist(artist)
        result_artist = await dal.get_artist_by_tm_id("gosha_tm_id")

        assert result_artist
        assert result_artist.name == "gosha"
        assert result_artist.tickets_link == "https://gosha_tickets.com/"

    async def test_same_tm_id_fails(
        self, dal: DAL, get_artist_update: Callable[[str], ArtistUpdate]
    ) -> None:
        artist_1 = get_artist_update("gosha")
        artist_2 = get_artist_update("clara")
        artist_2.source_specific_data[EventSource.ticketmaster_api][
            "id"
        ] = "gosha_tm_id"
        await dal.add_artist(artist_1)
        with pytest.raises(IntegrityError):
            await dal.add_artist(artist_2)


if __name__ == "__main__":
    pytest.main()
