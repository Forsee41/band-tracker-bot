from datetime import datetime

from band_tracker.core.enums import EventType


class EventStats:
    listing_count: int
    avg_price: int
    lowest_price: int
    highest_price: int


class Event:
    id: str
    name: str
    artists: list[str]
    date: datetime
    venue: str
    stats: EventStats
    title: str
    type_: EventType
    rating: float

    @property
    def has_passed(self) -> bool:
        return self.date <= datetime.now()
