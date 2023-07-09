from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from band_tracker.core.interfaces import DAL

if TYPE_CHECKING:
    from band_tracker.core.artist import Artist


@dataclass
class Event:
    title: str
    date: datetime
    venue: str
    venue_city: str
    venue_country: str
    ticket_url: str | None
    artist_ids: list[str]

    def get_artists(self, dal: DAL) -> list["Artist"]:
        assert dal
        raise NotImplementedError
