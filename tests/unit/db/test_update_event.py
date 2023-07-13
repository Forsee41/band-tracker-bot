from datetime import datetime
from typing import Callable

import pytest

from band_tracker.core.event import Event, EventSales
from band_tracker.core.event_update import EventUpdate
from band_tracker.db.dal import DAL


class TestUpdateEventDAL:
    async def test_event_update(
        self, dal: DAL, get_event_update: Callable[[str], EventUpdate]
    ) -> None:
        update_event = get_event_update("fest")

        await dal.add_event(update_event)
        update_event.sales.sale_start = datetime(8045, 4, 5)
        update_event.sales.sale_end = datetime(8045, 4, 6)
        await dal.update_event(update_event)

        result_event = await dal.get_event_by_tm_id("fest_tm_id")
        db_id = result_event.id
        event = Event(
            id=db_id,
            title="fest",
            date=datetime(2025, 4, 23),
            venue="Grant Park",
            venue_city="Chicago",
            venue_country="USA",
            image="https://grand_park_img_1.com/",
            ticket_url="https://fest_ticket_url.com/",
            sales=EventSales(
                sale_start=datetime(8045, 4, 5),
                sale_end=datetime(8045, 4, 6),
                price_max=None,
                price_min=150.0,
                currency="usd",
            ),
        )

        assert result_event == event


if __name__ == "__main__":
    pytest.main()
