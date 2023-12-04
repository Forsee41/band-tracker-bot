from typing import Callable
from uuid import UUID

import pytest

from band_tracker.core.user import User
from band_tracker.db.artist_update import ArtistUpdate
from band_tracker.db.dal_bot import BotDAL
from band_tracker.db.dal_update import UpdateDAL
from band_tracker.db.event_update import EventUpdate

UserFixture = Callable[[int, str], User]


async def test_counts_correctly(
    update_dal: UpdateDAL,
    get_artist_update: Callable[[str], ArtistUpdate],
    bot_dal: BotDAL,
    get_event_update: Callable[[str], EventUpdate],
) -> None:
    artist_names = ["gosha", "clara", "anton"]
    artist_updates = [get_artist_update(artist) for artist in artist_names]
    uuids: list[UUID] = []
    for artist in artist_updates:
        uuid = await update_dal._add_artist(artist)
        uuids.append(uuid)
    clara_artist_id = uuids[1]
    events = ["concert", "fest", "eurovision"]
    for event in events:
        update_event = get_event_update(event)
        await update_dal._add_event(update_event)
    result = await bot_dal.get_artist_events_amount(artist_id=clara_artist_id)

    assert result == 2


async def test_zero_events_count(
    update_dal: UpdateDAL,
    get_artist_update: Callable[[str], ArtistUpdate],
    bot_dal: BotDAL,
    get_event_update: Callable[[str], EventUpdate],
) -> None:
    artist_names = ["gosha", "clara", "anton"]
    artist_updates = [get_artist_update(artist) for artist in artist_names]
    uuids: list[UUID] = []
    for artist in artist_updates:
        uuid = await update_dal._add_artist(artist)
        uuids.append(uuid)
    clara_artist_id = uuids[1]
    events = ["concert"]
    for event in events:
        update_event = get_event_update(event)
        await update_dal._add_event(update_event)
    result = await bot_dal.get_artist_events_amount(artist_id=clara_artist_id)

    assert result == 0


if __name__ == "__main__":
    pytest.main()
