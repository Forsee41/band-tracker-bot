from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Optional
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
    venue: str | None
    venue_city: str | None
    venue_country: str | None
    ticket_url: str | None
    artist_ids: list[UUID]
    image: str | None
    thumbnail: str | None
    last_update: datetime
    sales: EventSales

    @property
    def on_sale(self) -> bool:
        sale_start = self.sales.sale_start
        sale_end = self.sales.sale_end
        if sale_start is not None and sale_end is not None:
            return (sale_start <= datetime.now()) and (sale_end >= datetime.now())
        else:
            return False

    async def get_artists(self, dal: DAL) -> list[Optional["Artist"]]:
        result_artists = []
        for i in self.artist_ids:
            result_artists.append(await dal.get_artist(i))

        return result_artists
