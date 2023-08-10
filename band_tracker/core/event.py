from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from band_tracker.core.interfaces import DAL

if TYPE_CHECKING:
    from band_tracker.core.artist import Artist


@dataclass
class EventSales:
    sale_start: datetime | None
    sale_end: datetime | None
    price_max: float | None
    price_min: float | None
    currency: str | None


@dataclass
class Event:
    id: UUID
    title: str
    date: datetime
    venue: str
    venue_city: str
    venue_country: str
    ticket_url: str | None
    artist_ids: list[UUID]
    image: str | None
    sales: EventSales

    @property
    def on_sale(self) -> bool:
        sale_start = self.sales.sale_start
        sale_end = self.sales.sale_end
        if sale_start is not None and sale_end is not None:
            return (sale_start <= datetime.now()) and (sale_end >= datetime.now())
        else:
            return False

    def get_artists(self, dal: DAL) -> list["Artist"]:
        assert dal
        raise NotImplementedError
