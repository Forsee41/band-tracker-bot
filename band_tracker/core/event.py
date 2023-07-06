from datetime import datetime

from pydantic import BaseModel, HttpUrl


class Event(BaseModel):
    id: str
    title: str
    date: datetime
    venue: str
    ticket_url: HttpUrl | None

    @property
    def has_passed(self) -> bool:
        return self.date <= datetime.now()

    @property
    def is_available(self) -> bool:
        return self.stats.listing_count > 0
