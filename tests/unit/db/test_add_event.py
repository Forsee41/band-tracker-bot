from typing import Callable

import pytest

from band_tracker.core.artist_update import ArtistUpdate
from band_tracker.core.event_update import EventUpdate
from band_tracker.db.dal import DAL


class TestAddEventDAL:
    async def test__link_event_to_artists(
        self,
        dal: DAL,
        get_event_update: Callable[[str], EventUpdate],
        get_artist_update: Callable[[str], ArtistUpdate],
    ) -> None:
        for i in ["gosha", "anton", "clara"]:
            artist = get_artist_update(i)
            await dal._add_artist(artist)
        artists_tm_ids = ["anton_tm_id", "clara_tm_id", "gosha_tm_id"]
        update_event = get_event_update("eurovision")
        await dal.add_event(update_event)

        linked_artist = await dal._link_event_to_artists(
            "eurovision_tm_id", artists_tm_ids
        )
        assert linked_artist == artists_tm_ids

        linked_artist2 = await dal._link_event_to_artists(
            "eurovision_tm_id", artists_tm_ids, return_skipped=True
        )
        assert linked_artist2 == []

    async def test_get_event_by_id(
        self,
        dal: DAL,
        get_event_update: Callable[[str], EventUpdate],
        get_artist_update: Callable[[str], ArtistUpdate],
    ) -> None:
        for i in ["gosha", "anton", "clara"]:
            artist = get_artist_update(i)
            await dal._add_artist(artist)

        update_event = get_event_update("eurovision")
        await dal.add_event(update_event)

        event = await dal.get_event_by_tm_id("eurovision_tm_id")

        assert event
        result_event = await dal.get_event_by_id(event.id)
        assert result_event == event

    async def test_add_event(
        self,
        dal: DAL,
        get_event_update: Callable[[str], EventUpdate],
        get_artist_update: Callable[[str], ArtistUpdate],
    ) -> None:
        artist = get_artist_update("anton")
        await dal._add_artist(artist)

        update_event = get_event_update("concert")
        await dal.add_event(update_event)
        result_event = await dal.get_event_by_tm_id("concert_tm_id")

        assert result_event
        assert result_event.title == "concert"
        assert result_event.artist_ids


if __name__ == "__main__":
    pytest.main()
