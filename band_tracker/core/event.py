from dataclasses import dataclass
from datetime import datetime

from band_tracker.core.enums import EventType


@dataclass
class EventStats:
    listing_count: int
    avg_price: int
    lowest_price: int
    highest_price: int


@dataclass
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

    @property
    def is_available(self) -> bool:
        return self.stats.listing_count > 0
