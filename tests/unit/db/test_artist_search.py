from typing import Callable

import pytest

from band_tracker.db.artist_update import ArtistUpdate
from band_tracker.db.dal import UpdateDAL
from band_tracker.db.dal_bot import BotDAL


class TestArtistTextSearch:
    @pytest.mark.parametrize(
        ("search_str", "similarity", "expected_result"),
        (
            ["osha", 0.2, ["gosha"]],
            ["gos", 0.3, ["gosha"]],
            ["toh", 0.4, ["anton"]],
            ["clarnet", 0.9, ["clara"]],
            ["cal", 0.2, ["clara"]],
            ["a", -0.5, ["gosha", "anton", "clara"]],
        ),
    )
    async def test_basic_search(
        self,
        update_dal: UpdateDAL,
        get_artist_update: Callable[[str], ArtistUpdate],
        bot_dal: BotDAL,
        search_str: str,
        similarity: float,
        expected_result: list[str],
    ) -> None:
        artist_names = ["gosha", "clara", "anton"]
        artist_updates = [get_artist_update(artist) for artist in artist_names]
        for artist in artist_updates:
            await update_dal._add_artist(artist)
        result_artists = await bot_dal.search_artist(
            search_str, similarity_min=similarity
        )
        result = [artist.name for artist in result_artists]
        assert set(result) == set(expected_result)

    async def test_search_similar_aliases(
        self,
        update_dal: UpdateDAL,
        get_artist_update: Callable[[str], ArtistUpdate],
        bot_dal: BotDAL,
    ) -> None:
        artist_names = ["gosha", "clara", "anton"]
        gosha, clara, anton = [get_artist_update(artist) for artist in artist_names]
        gosha.aliases.append("goshturbator")
        anton.aliases.append("anturbator")
        for artist in gosha, anton, clara:
            await update_dal._add_artist(artist)
        result_artists = await bot_dal.search_artist("turbator", similarity_min=0.3)
        result = [artist.name for artist in result_artists]
        assert set(result) == set(["gosha", "anton"])


if __name__ == "__main__":
    pytest.main()
