from typing import Callable
from uuid import UUID

import pytest

from band_tracker.db.artist_update import ArtistUpdate
from band_tracker.db.dal_bot import BotDAL
from band_tracker.db.dal_update import UpdateDAL


async def test_returns_all_names(
    update_dal: UpdateDAL,
    get_artist_update: Callable[[str], ArtistUpdate],
    bot_dal: BotDAL,
) -> None:
    artist_names = ["gosha", "clara", "anton"]
    artist_updates = [get_artist_update(artist) for artist in artist_names]
    uuids: list[UUID] = []
    for artist in artist_updates:
        uuid = await update_dal._add_artist(artist)
        uuids.append(uuid)
    result = await bot_dal.get_artist_names(uuids)
    assert len(result) == 3
    assert result[uuids[0]] == "gosha"
    assert result[uuids[1]] == "clara"
    assert result[uuids[2]] == "anton"


if __name__ == "__main__":
    pytest.main()
