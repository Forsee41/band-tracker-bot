from typing import Callable

import pytest

from band_tracker.core.artist_update import ArtistUpdate
from band_tracker.db.dal import DAL


class TestDAL:
    async def test_add_artist(
        self, dal: DAL, get_artist_update: Callable[[str], ArtistUpdate]
    ) -> None:
        artist = get_artist_update("gosha")
        await dal.add_artist(artist)
        result_artist = await dal.get_artist_by_tm_id("gosha_tm_id")

        assert result_artist
        assert result_artist.name == "gosha"
        assert result_artist.tickets_link == "https://gosha_tickets.com/"


if __name__ == "__main__":
    pytest.main()
