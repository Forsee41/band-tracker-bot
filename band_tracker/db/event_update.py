from datetime import datetime
from typing import Any, TypeAlias

from pydantic import BaseModel, Field, NonNegativeFloat, StrictStr, field_validator

from band_tracker.core.enums import EventSource

SourceSpecificEventData: TypeAlias = dict[EventSource, dict[str, Any]]


class EventUpdateSales(BaseModel):
    sale_start: datetime | None
    sale_end: datetime | None
    price_max: NonNegativeFloat | None
    price_min: NonNegativeFloat | None
    currency: StrictStr | None


class EventUpdate(BaseModel):
    title: StrictStr
    date: datetime
    artists: list[str] = Field([])
    venue: StrictStr | None = Field(None)
    venue_city: StrictStr | None = Field(None)
    venue_country: StrictStr | None = Field(None)
    image: str | None = Field(None)
    ticket_url: str | None = Field(None)
    source_specific_data: SourceSpecificEventData = Field(
        {EventSource.ticketmaster_api: {}}
    )
    sales: EventUpdateSales = Field(
        EventUpdateSales(
            sale_start=None,
            sale_end=None,
            price_max=None,
            price_min=None,
            currency=None,
        )
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

    def on_sale(self) -> bool:
        sale_start = self.sales.sale_start
        sale_end = self.sales.sale_end
        if sale_start is not None and sale_end is not None:
            return (sale_start <= datetime.now()) and (sale_end >= datetime.now())
        else:
            return False
