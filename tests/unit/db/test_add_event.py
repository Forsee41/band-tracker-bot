from typing import Callable

import pytest

from band_tracker.core.event_update import EventUpdate
from band_tracker.db.dal import DAL


class TestAddEventDAL:
    async def test_add_event(
        self, dal: DAL, get_event_update: Callable[[str], EventUpdate]
    ) -> None:
        update_event = get_event_update("concert")
        await dal.add_event(update_event)
        result_event = await dal.get_event_by_tm_id("concert_tm_id")

        assert result_event.title == "concert"
        assert result_event.artist_ids == ["anton_tm_id"]


if __name__ == "__main__":
    pytest.main()
