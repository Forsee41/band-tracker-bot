from typing import Callable
from uuid import UUID

import pytest

from band_tracker.core.user import User
from band_tracker.db.artist_update import ArtistUpdate
from band_tracker.db.dal_bot import BotDAL
from band_tracker.db.dal_update import UpdateDAL
from band_tracker.db.event_update import EventUpdate

UserFixture = Callable[[int, str], User]


@pytest.mark.debug
async def test_returns_required_events(
    update_dal: UpdateDAL,
    get_artist_update: Callable[[str], ArtistUpdate],
    bot_dal: BotDAL,
    user: UserFixture,
    get_event_update: Callable[[str], EventUpdate],
) -> None:
    artist_names = ["gosha", "clara", "anton"]
    artist_updates = [get_artist_update(artist) for artist in artist_names]
    uuids: list[UUID] = []
    for artist in artist_updates:
        uuid = await update_dal._add_artist(artist)
        uuids.append(uuid)
    clara_artist_id = uuids[1]
    added_user = user(1, "user1")
    await bot_dal.add_user(added_user)
    await bot_dal.add_follow(user_tg_id=added_user.id, artist_id=clara_artist_id)
    events = ["concert", "fest", "eurovision"]
    for event in events:
        update_event = get_event_update(event)
        await update_dal._add_event(update_event)
    result = await bot_dal.get_all_events_for_user(user_tg_id=1)

    assert len(result) == 2
    assert result[0].title == "fest" or result[1].title == "fest"
    assert result[0].title == "eurovision" or result[1].title == "eurovision"


if __name__ == "__main__":
    pytest.main()
