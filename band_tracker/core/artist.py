from typing import Optional

from pydantic import BaseModel, HttpUrl, NonNegativeInt, field_validator

from band_tracker.core.enums import EventSource


class Artist(BaseModel):
    id: Optional[str] = None
    name: str
    spotify_link: HttpUrl | None
    tickets_link: HttpUrl | None
    inst_link: HttpUrl | None
    youtube_link: HttpUrl | None
    upcoming_events_amount: NonNegativeInt
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
        id_api = values.get("id")
        if not (id_api or id_db):
            raise ValueError("either one of the id's should be defined")
        return _source_specific_data_value

    def get_source_specific_data(self, source: EventSource) -> dict:
        """
        Returns a source-specific data of an Artist (like specific id, slug, etc.),
        or an empty dict if one is not present
        """
        if source in self._source_specific_data:
            return self._source_specific_data[source]
        else:
            return {}

    @property
    def has_upcoming_events(self) -> bool:
        return self.upcoming_events_amount > 0
