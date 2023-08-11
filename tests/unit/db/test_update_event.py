from datetime import datetime
from typing import Callable

import pytest

from band_tracker.core.artist_update import ArtistUpdate
from band_tracker.core.event_update import EventUpdate
from band_tracker.db.dal import DAL


class TestUpdateEventDAL:
    async def test_event_update(
        self,
        dal: DAL,
        get_event_update: Callable[[str], EventUpdate],
        get_artist_update: Callable[[str], ArtistUpdate],
    ) -> None:
        for i in ["anton", "clara"]:
            artist = get_artist_update(i)
            await dal.add_artist(artist)

        update_event = get_event_update("fest")

        new_artist = get_artist_update("gosha")
        await dal.add_artist(new_artist)

        await dal.add_event(update_event)

        update_event.artists += ["gosha_tm_id"]

        update_event.sales.sale_start = datetime(8045, 4, 5)
        update_event.sales.sale_end = datetime(8045, 4, 6)

        update_event.image = None

        await dal.update_event(update_event)

        result_event = await dal.get_event_by_tm_id("fest_tm_id")
        assert result_event
        assert result_event.image is None
        assert result_event.title == "fest"
        assert result_event.venue_country == "USA"
        assert result_event.sales.sale_start == datetime(8045, 4, 5)
        assert result_event.artist_ids

        result_artists = await result_event.get_artists(dal)
        assert [i.name for i in result_artists if i is not None] == [
            "anton",
            "clara",
            "gosha",
        ]

    async def test_add_new_event(
        self,
        dal: DAL,
        get_event_update: Callable[[str], EventUpdate],
        get_artist_update: Callable[[str], ArtistUpdate],
    ) -> None:
        artists = ["gosha", "anton", "clara"]
        for i in artists:
            artist = get_artist_update(i)

            await dal.add_artist(artist)

        update_event = get_event_update("eurovision")
        await dal.update_event(update_event)

        result_event = await dal.get_event_by_tm_id("eurovision_tm_id")
        assert result_event

    async def test_update_defect_events(
        self,
        dal: DAL,
        get_event_update: Callable[[str], EventUpdate],
        get_artist_update: Callable[[str], ArtistUpdate],
    ) -> None:
        for i in ["anton", "clara"]:
            artist = get_artist_update(i)
            await dal.add_artist(artist)

        update_event = get_event_update("fest")

        await dal.add_event(update_event)

        update_event.ticket_url = None
        update_event.title = "Sodom"
        await dal.update_event(update_event)

        result_event = await dal.get_event_by_tm_id("fest_tm_id")
        assert result_event
        assert result_event.title == "Sodom"
        assert result_event.ticket_url == "https://fest_ticket_url.com/"

    async def test_linking_new_artists(
        self,
        dal: DAL,
        get_event_update: Callable[[str], EventUpdate],
        get_artist_update: Callable[[str], ArtistUpdate],
    ) -> None:
        for i in ["anton", "clara"]:
            artist = get_artist_update(i)
            await dal.add_artist(artist)

        update_event = get_event_update("fest")
        await dal.add_event(update_event)

        update_event.artists += ["gosha_tm_id"]

        linked_artist = await dal._link_event_to_artists(
            "fest_tm_id",
            ["anton_tm_id", "clara_tm_id", "gosha_tm_id"],
            return_skipped=True,
        )
        assert linked_artist == ["gosha_tm_id"]

        new_artist = get_artist_update("gosha")
        await dal.add_artist(new_artist)

        await dal.update_event(update_event)

        linked_artist = await dal._link_event_to_artists(
            "fest_tm_id",
            ["anton_tm_id", "clara_tm_id", "gosha_tm_id"],
            return_skipped=True,
        )
        assert linked_artist == []


if __name__ == "__main__":
    pytest.main()
