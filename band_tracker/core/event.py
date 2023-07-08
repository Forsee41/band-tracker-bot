from datetime import datetime
from typing import Any, Optional, TypeAlias

from pydantic import (
    BaseModel,
    Field,
    FieldValidationInfo,
    HttpUrl,
    StrictStr,
    field_validator,
)

from band_tracker.core.enums import EventSource

SourceSpecificEventData: TypeAlias = dict[EventSource, dict[str, Any]]


class Event(BaseModel):
    id: Optional[str] = None
    title: StrictStr
    date: datetime = Field(None)
    venue: StrictStr
    ticket_url: HttpUrl = Field(None)
    source_specific_data: SourceSpecificEventData = Field(
        {EventSource.ticketmaster_api: {}}
    )
    venue_city: StrictStr = Field(None)
    venue_country: StrictStr = Field(None)

    @field_validator("source_specific_data")
    def id_presence(
        cls,
        _source_specific_data_value: SourceSpecificEventData,
        values: FieldValidationInfo,
    ) -> SourceSpecificEventData:
        ticketmaster_data = _source_specific_data_value.get(
            EventSource.ticketmaster_api
        )
        ticketmaster_id = ticketmaster_data["id"] if ticketmaster_data else None
        id_api = values.data.get("id")
        if not (id_api or ticketmaster_id):
            raise ValueError("either one of the id's should be defined")
        return _source_specific_data_value

    @property
    def has_passed(self) -> bool:
        return self.date <= datetime.now()
