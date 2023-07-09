from datetime import datetime
from typing import Any, TypeAlias

from pydantic import BaseModel, Field, HttpUrl, StrictStr, field_validator

from band_tracker.core.enums import EventSource

SourceSpecificEventData: TypeAlias = dict[EventSource, dict[str, Any]]


class EventUpdate(BaseModel):
    title: StrictStr
    date: datetime
    artists: list[str] = Field([])
    venue: StrictStr
    venue_city: StrictStr
    venue_country: StrictStr
    ticket_url: HttpUrl | None = Field(None)
    source_specific_data: SourceSpecificEventData = Field(
        {EventSource.ticketmaster_api: {}}
    )

    @field_validator("source_specific_data")
    def id_presence(
        cls,
        _source_specific_data_value: SourceSpecificEventData,
    ) -> SourceSpecificEventData:
        ticketmaster_data = _source_specific_data_value.get(
            EventSource.ticketmaster_api
        )
        ticketmaster_id = ticketmaster_data["id"] if ticketmaster_data else None
        if not ticketmaster_id:
            raise ValueError("Update should have source-specific id")
        return _source_specific_data_value
