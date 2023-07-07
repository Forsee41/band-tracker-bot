from datetime import datetime
from typing import Optional

from pydantic import BaseModel, HttpUrl, field_validator

from band_tracker.core.enums import EventSource


class Event(BaseModel):
    id: Optional[str] = None
    title: str
    date: datetime
    venue: str
    ticket_url: HttpUrl | None
    source_specific_data: dict[EventSource, dict] = lambda: dict[
        EventSource.ticketmaster_api, {}
    ]

    @field_validator("id")
    def prevent_Id_to_be_None(cls, id_value):
        assert id_value is not None, "id must not be None"
        return id_value

    @field_validator("source_specific_data")
    def id_presence(cls, _source_specific_data_value, values):
        id_db = _source_specific_data_value.get(EventSource.ticketmaster_api).get("id")
        id_api = values.data.get("id")
        if not (id_api or id_db):
            raise ValueError("either one of the id's should be defined")
        return _source_specific_data_value

    @property
    def has_passed(self) -> bool:
        return self.date <= datetime.now()

    @property
    def is_available(self) -> bool:
        return self.stats.listing_count > 0
