from typing import Any, TypeAlias

from pydantic import BaseModel, Field, HttpUrl, StrictStr, field_validator

from band_tracker.core.enums import EventSource

SourceSpecificArtistData: TypeAlias = dict[EventSource, dict[str, Any]]


class ArtistUpdateSocials(BaseModel):
    instagram: HttpUrl | None
    youtube: HttpUrl | None
    spotify: HttpUrl | None


class ArtistUpdate(BaseModel):
    name: StrictStr
    socials: ArtistUpdateSocials = ArtistUpdateSocials(
        instagram=None, youtube=None, spotify=None
    )
    tickets_link: HttpUrl | None = Field(None)
    source_specific_data: SourceSpecificArtistData = Field(
        {EventSource.ticketmaster_api: {}}
    )
    images: HttpUrl | None = Field(None)
    genres: list[str] = Field([])
    aliases: list[str] = Field([])

    @field_validator("source_specific_data")
    def id_presence(
        cls,
        _source_specific_data_value: SourceSpecificArtistData,
    ) -> dict[EventSource, dict]:
        ticketmaster_data = _source_specific_data_value.get(
            EventSource.ticketmaster_api
        )
        ticketmaster_id = ticketmaster_data["id"] if ticketmaster_data else None
        if not ticketmaster_id:
            raise ValueError("Update should have source-specific id")
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
