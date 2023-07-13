from datetime import datetime
from typing import Callable

import pytest

from band_tracker.core.event import Event, EventSales
from band_tracker.core.event_update import EventUpdate
from band_tracker.db.dal import DAL


class TestAddEventDAL:
    async def test_add_event(
        self, dal: DAL, get_event_update: Callable[[str], EventUpdate]
    ) -> None:
        update_event = get_event_update("concert")
        await dal.add_event(update_event)
        result_event = await dal.get_event_by_tm_id("concert_tm_id")
        db_id = result_event.id
        event = Event(
            id=db_id,
            title="concert",
            date=datetime(2024, 4, 23),
            venue="The Dome Of Paris",
            venue_city="Paris",
            venue_country="France",
            image="https://dome_of_paris_img_1.com/",
            ticket_url="https://concert_ticket_url.com/",
            sales=EventSales(
                sale_start=None,
                sale_end=None,
                price_max=150.0,
                price_min=100.0,
                currency="eur",
            ),
        )

        assert result_event == event


if __name__ == "__main__":
    pytest.main()
