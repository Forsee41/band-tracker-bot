from pydantic import BaseModel, HttpUrl, NonNegativeInt

from band_tracker.core.enums import EventSource


class Artist(BaseModel):
    id: str
    name: str
    spotify_link: HttpUrl | None
    tickets_link: HttpUrl | None
    inst_link: HttpUrl | None
    youtube_link: HttpUrl | None
    upcoming_events_amount: NonNegativeInt
    _source_specific_data: dict[EventSource, dict] | None = lambda: dict[
        EventSource.ticketmaster_api, dict
    ]

    def get_source_specific_data(self, source: EventSource) -> dict:
        """
        Returns a source-specific data of an Artist (like specific id, slug, etc.),
        or an empty dict if one is not present
        """
        if source in self._source_specific_data:
            return self._source_specific_data[source]
        else:
            return None

    @property
    def has_upcoming_events(self) -> bool:
        return self.upcoming_events_amount > 0
