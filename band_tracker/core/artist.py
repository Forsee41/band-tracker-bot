from typing import Any, TypeAlias

from pydantic import (
    BaseModel,
    Field,
    FieldValidationInfo,
    HttpUrl,
    StrictStr,
    field_validator,
)

from band_tracker.core.enums import EventSource

SourceSpecificArtistData: TypeAlias = dict[EventSource, dict[str, Any]]


class Artist(BaseModel):
    id: str | None = None
    name: StrictStr
    socials: dict[str, HttpUrl | None] = Field({})
    tickets_link: HttpUrl | None = Field(None)
    source_specific_data: SourceSpecificArtistData = Field(
        {EventSource.ticketmaster_api: {}}
    )
    images: list[HttpUrl] = Field([])
    genres: list[str] | None = Field(None)
    aliases: list[str] | None = Field(None)

    @field_validator("socials")
    def validate_socials(cls, value: dict[str, HttpUrl]) -> dict[str, HttpUrl]:
        if value != {}:
            required_keys = {"instagram", "youtube", "spotify"}
            if set(value.keys()) != required_keys:
                raise ValueError(
                    "socials must contain keys for Instagram, YouTube, and Spotify"
                )
        return value

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
