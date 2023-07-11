from datetime import datetime
from typing import Any, TypeAlias

from pydantic import (
    BaseModel,
    Field,
    HttpUrl,
    NonNegativeFloat,
    StrictStr,
    field_validator,
)

from band_tracker.core.enums import EventSource

SourceSpecificEventData: TypeAlias = dict[EventSource, dict[str, Any]]


class EventUpdateSales(BaseModel):
    on_sale: bool | None
    price_max: NonNegativeFloat | None
    price_min: NonNegativeFloat | None
    currency: StrictStr | None


class EventUpdate(BaseModel):
    title: StrictStr
    date: datetime
    artists: list[str] = Field([])
    venue: StrictStr
    venue_city: StrictStr
    venue_country: StrictStr
    images: list[HttpUrl] = Field([])
    ticket_url: HttpUrl | None = Field(None)
    source_specific_data: SourceSpecificEventData = Field(
        {EventSource.ticketmaster_api: {}}
    )
    sales: EventUpdateSales = Field(
        EventUpdateSales(on_sale=None, price_max=None, price_min=None, currency=None)
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

    def get_source_specific_data(self, source: EventSource) -> dict:
        """
        Returns a source-specific data of an Event,
        or an empty dict if one is not present
        """
        if source in self.source_specific_data:
            return self.source_specific_data[source]
        else:
            return {}
