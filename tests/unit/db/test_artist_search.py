from typing import Callable

import pytest

from band_tracker.db.artist_update import ArtistUpdate
from band_tracker.db.dal import BotDAL, UpdateDAL


class TestAddArtistDAL:
    async def test_add_artist(
        self, update_dal: UpdateDAL, get_artist_update: Callable[[str], ArtistUpdate]
    ) -> None:
        artist = get_artist_update("gosha")
        await update_dal._add_artist(artist)
        result_artist = await update_dal._get_artist_by_tm_id("gosha_tm_id")

        assert result_artist
        assert result_artist.name == "gosha"
        assert result_artist.tickets_link == "https://gosha_tickets.com/"

    async def test_same_tm_id_fails(
        self,
        update_dal: UpdateDAL,
        get_artist_update: Callable[[str], ArtistUpdate],
        bot_dal: BotDAL,
    ) -> None:
        artist_names = ["gosha", "clara", "anton"]
        artist_updates = [get_artist_update(artist) for artist in artist_names]
        for artist in artist_updates:
            await update_dal._add_artist(artist)
        result = await bot_dal.search_artist("gosa", similarity_min=0.3)
        assert result == ["gosha"]


if __name__ == "__main__":
    pytest.main()
