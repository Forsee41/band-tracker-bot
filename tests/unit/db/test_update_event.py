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
            await dal._add_artist(artist)

        update_event = get_event_update("fest")

        await dal._add_event(update_event)
        update_event.sales.sale_start = datetime(8045, 4, 5)
        update_event.sales.sale_end = datetime(8045, 4, 6)
        await dal.update_event(update_event)

        result_event = await dal.get_event_by_tm_id("fest_tm_id")
        assert result_event
        assert result_event.title == "fest"
        assert result_event.venue_country == "USA"
        assert result_event.sales.sale_start == datetime(8045, 4, 5)
        assert result_event.artist_ids


if __name__ == "__main__":
    pytest.main()
