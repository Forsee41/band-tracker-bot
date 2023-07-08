from typing import Any, Optional, TypeAlias

from pydantic import BaseModel, FieldValidationInfo, HttpUrl, field_validator

from band_tracker.core.enums import EventSource

SourceSpecificArtistData: TypeAlias = dict[EventSource, dict[str, Any]]


class Artist(BaseModel):
    id: Optional[str] = None
    name: str
    spotify_link: HttpUrl | None
    tickets_link: HttpUrl | None
    inst_link: HttpUrl | None
    youtube_link: HttpUrl | None
    source_specific_data: SourceSpecificArtistData = {EventSource.ticketmaster_api: {}}
    images: list[HttpUrl] = []

    @field_validator("source_specific_data")
    def id_presence(
        cls,
        _source_specific_data_value: SourceSpecificArtistData,
        values: FieldValidationInfo,
    ) -> dict[EventSource, dict]:
        ticketmaster_data = _source_specific_data_value.get(
            EventSource.ticketmaster_api
        )
        ticketmaster_id = ticketmaster_data["id"] if ticketmaster_data else None
        id_api = values.data.get("id")
        if not (id_api or ticketmaster_id):
            raise ValueError("either one of the id's should be defined")
        return _source_specific_data_value

    def get_source_specific_data(self, source: EventSource) -> dict:
        """
        Returns a source-specific data of an Artist (like specific id, slug, etc.),
        or an empty dict if one is not present
        """
        if source in self.source_specific_data:
            return self.source_specific_data[source]
        else:
            return {}
